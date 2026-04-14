"""
Gmeeting UAT — 添加会议并提交审批
端到端流程：登录 → 解析枚举 → 创建会议 → 提交审批 → 验证审批中

用法：
    python add_meeting.py --session-id <id>   # 从 CSV 读取字段值
    python add_meeting.py                      # 直接用 config.py 默认值（调试用）
"""
import sys
import argparse
import requests

from config import DEFAULT_CONFIG
from auth import login
from api import (
    get_departments, get_therapy_areas, get_products,
    get_provinces, get_cities,
    find_id,
)
from form_session import read_csv

# 会议类别/形式/举办地 映射（中文 → API 值）
_MEETING_CATEGORY_MAP = {"全国会": "National", "区域会": "Regional", "城市会": "City"}
_MEETING_METHOD_MAP = {"线下会议": "Offline", "线上会议": "Online", "Hybrid会议": "Hybrid"}
_VENUE_TYPE_MAP = {"单点会": "single", "多点会": "multi"}
_LOCATION_TYPE_MAP = {"酒店": "hotel", "医院": "hospital", "餐厅": "restaurant"}


# ── 步骤函数 ──────────────────────────────────────────────

def resolve_ids(session: requests.Session, cfg: dict) -> dict:
    """将配置中的中文名称解析为 API 所需的 ID/code"""
    print("[resolve] 获取枚举数据...")

    depts = get_departments(session, cfg)
    dept_id = find_id(depts, cfg["department"], name_key="buNameCn", id_key="bu")

    tas = get_therapy_areas(session, cfg)
    ta_id = find_id(tas, cfg["therapy_area"], name_key="taNameCn", id_key="ta")

    products = get_products(session, ta_id, cfg)
    product_ids = [find_id(products, p, name_key="prodName", id_key="prodCode") for p in cfg["products"]]

    provinces = get_provinces(session, cfg)
    province_id = find_id(provinces, cfg["province"], name_key="name", id_key="id")

    cities = get_cities(session, province_id, cfg)
    city_id = find_id(cities, cfg["city"], name_key="name", id_key="id")

    print(f"[resolve] dept={dept_id}, ta={ta_id}, products={product_ids}, "
          f"province={province_id}, city={city_id}")

    return {
        "dept_id": dept_id,
        "ta_id": ta_id,
        "product_ids": product_ids,
        "province_id": province_id,
        "city_id": city_id,
    }


def create_meeting(session: requests.Session, cfg: dict, ids: dict):
    """创建会议 — POST /planning/meeting/newCreate，返回 (meeting_id, year, season)"""
    print("[create] 创建会议...")

    year, month = cfg["start_month"].split("-")
    season = str((int(month) - 1) // 3 + 1)

    product_code = ids["product_ids"][0]
    brand_budget = cfg["brand_budgets"].get(cfg["products"][0], cfg["total_budget"])

    payload = {
        "name": cfg["meeting_name"],
        "bu": ids["dept_id"],
        "ta": ids["ta_id"],
        "product": product_code,
        "meetingCategory": _MEETING_CATEGORY_MAP.get(cfg["meeting_type"], cfg["meeting_type"]),
        "meetingMethod": _MEETING_METHOD_MAP.get(cfg["meeting_format"], cfg["meeting_format"]),
        "venueType": _VENUE_TYPE_MAP.get(cfg["location_type"], cfg["location_type"]),
        "locationType": _LOCATION_TYPE_MAP.get(cfg["venue_type"], cfg["venue_type"]),
        "startYearMonth": cfg["start_month"],
        "province": ids["province_id"],
        "city": ids["city_id"],
        "paidSpeaker": cfg["speakers_total"],
        "numberOfPlanOfflineSpeaker": cfg["speakers_offline"],
        "hcpAttendee": cfg["attendees_total"],
        "numberOfPlanOfflineAttendee": cfg["attendees_offline"],
        "totalBudget": cfg["total_budget"],
        "products": [{"product": product_code, "budget": brand_budget}],
        "selectedProductList": [{"product": product_code, "budget": brand_budget}],
        "unpaidSpeaker": 0,
        "year": year,
        "season": season,
    }

    resp = session.post(
        f"{cfg['api_base']}/planning/meeting/newCreate",
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"创建会议失败: {data}")

    # API returns the new meeting ID in the "message" field, not "result"
    meeting_id = data.get("result") or data.get("message")
    print(f"[create] 会议创建成功，id={meeting_id}")
    return meeting_id, year, season


def submit_meeting(session: requests.Session, cfg: dict, meeting_id: str, year: str, season: str) -> None:
    """提交会议审批 — POST /planning/meeting/submit"""
    print(f"[submit] 提交审批，meeting_id={meeting_id}...")

    resp = session.post(
        f"{cfg['api_base']}/planning/meeting/submit",
        json={"ids": [meeting_id], "year": int(year), "season": int(season)},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"提交审批失败: {data}")
    print("[submit] 提交成功")


def verify_in_approval(session: requests.Session, cfg: dict, meeting_id: str, year: str, season: str) -> None:
    """验证会议出现在审批中列表 — POST /planning/meeting/searchList (searchMode=2)"""
    print("[verify] 验证审批中状态...")

    resp = session.post(
        f"{cfg['api_base']}/planning/meeting/searchList",
        json={"searchMode": "2", "season": int(season), "year": int(year), "isAddHoc": 0},
        timeout=15,
    )
    resp.raise_for_status()
    meetings = resp.json().get("result", [])
    ids = [m.get("id") for m in meetings]

    if meeting_id not in ids:
        raise AssertionError(
            f"会议 {meeting_id} 未出现在审批中列表，当前列表 id: {ids}"
        )
    print(f"[verify] 验证通过，会议 {meeting_id} 已进入审批中")


# ── 主流程 ────────────────────────────────────────────────

def run(cfg: dict) -> str:
    session = requests.Session()

    login(session, cfg)
    ids = resolve_ids(session, cfg)
    meeting_id, year, season = create_meeting(session, cfg, ids)
    submit_meeting(session, cfg, meeting_id, year, season)
    verify_in_approval(session, cfg, meeting_id, year, season)

    print("\n[done] 全流程完成：会议已进入审批中")
    return meeting_id


def parse_args():
    parser = argparse.ArgumentParser(description="Gmeeting UAT 添加会议自动化")
    parser.add_argument("--session-id", help="从 C:/tmp/gmeeting_<id>.csv 读取字段值")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.session_id:
        cfg = read_csv(args.session_id)
        print(f"[config] 从 CSV 加载配置，session_id={args.session_id}")
    else:
        cfg = dict(DEFAULT_CONFIG)
        print("[config] 使用 config.py 默认值")

    try:
        run(cfg)
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)
