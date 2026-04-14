"""
run_meeting — 读取 session CSV，执行完整流程：登录→枚举解析→创建→提交→验证

用法：
    python -m tools.run_meeting --session-id <session_id>

输出：
    成功时 stdout 打印 meeting_id
    失败时 stderr 打印错误，exit code 1
"""
import argparse
import csv
import json
import os
import sys
import uuid
import requests

# Windows 终端中文输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ── 默认配置 ──────────────────────────────────────────────
DEFAULT_CONFIG = {
    "env": "uat",
    "url": "https://gmeeting-dev.igskapp.com",
    "login_url": "https://gmeeting-dev.igskapp.com/#/login2",
    "api_base": "https://gmeeting-dev-api.igskapp.com/e2estservice",
    "username": "ttz79417",
    "password": "222222",
    "meeting_name": "测试会议-CNS-利必通-自动化",
    "department": "MA CO",
    "therapy_area": "CNS",
    "products": ["利必通"],
    "meeting_type": "全国会",
    "meeting_format": "线下会议",
    "location_type": "单点会",
    "venue_type": "酒店",
    "start_month": "2026-07",
    "province": "北京",
    "city": "北京",
    "speakers_total": 2,
    "speakers_offline": 2,
    "attendees_total": 20,
    "attendees_offline": 20,
    "total_budget": 10000,
    "brand_budgets": {"利必通": 10000},
}

FIELDS = [
    ("meeting_name",     "会议名称"),
    ("department",       "业务部门"),
    ("therapy_area",     "治疗领域"),
    ("products",         "产品名称"),
    ("meeting_type",     "会议类别"),
    ("meeting_format",   "会议形式"),
    ("location_type",    "单点会/多点会"),
    ("venue_type",       "举办地类别"),
    ("start_month",      "开始年月"),
    ("province",         "省/直辖市"),
    ("city",             "城市"),
    ("speakers_total",   "计划讲者人数"),
    ("speakers_offline", "计划讲者人数（线下）"),
    ("attendees_total",  "计划参会者人数"),
    ("attendees_offline","计划参会者人数（线下）"),
    ("total_budget",     "总预算"),
    ("brand_budgets",    "品牌预算"),
]

_TMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "temp")

# ── 枚举映射 ──────────────────────────────────────────────
_MEETING_CATEGORY_MAP = {"全国会": "National", "区域会": "Regional", "城市会": "City"}
_MEETING_METHOD_MAP   = {"线下会议": "Offline", "线上会议": "Online", "Hybrid会议": "Hybrid"}
_VENUE_TYPE_MAP       = {"单点会": "single", "多点会": "multi"}
_LOCATION_TYPE_MAP    = {"酒店": "hotel", "医院": "hospital", "餐厅": "restaurant"}

# ── HTTP 请求头 ────────────────────────────────────────────
_HEADERS = {
    "referer": "https://gmeeting-dev.igskapp.com/",
    "origin": "https://gmeeting-dev.igskapp.com",
    "accept-language": "zh",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    ),
}


# ── CSV 读取 ──────────────────────────────────────────────

def read_csv(session_id: str) -> dict:
    path = os.path.join(_TMP_DIR, f"gmeeting_{session_id}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Session CSV 不存在: {path}")

    raw = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw[row["field"]] = row["value"]

    cfg = dict(DEFAULT_CONFIG)
    for key, val in raw.items():
        if key not in cfg:
            continue
        default = DEFAULT_CONFIG[key]
        if isinstance(default, list):
            cfg[key] = [v.strip() for v in val.split(",") if v.strip()]
        elif isinstance(default, dict):
            d = {}
            for pair in val.split(","):
                if ":" in pair:
                    k, v = pair.split(":", 1)
                    d[k.strip()] = int(v.strip()) if v.strip().isdigit() else v.strip()
            cfg[key] = d
        elif isinstance(default, int):
            cfg[key] = int(val) if val.strip().isdigit() else default
        else:
            cfg[key] = val
    return cfg


# ── 认证 ──────────────────────────────────────────────────

def login(session: requests.Session, cfg: dict) -> None:
    session.headers.update(_HEADERS)
    resp = session.post(
        f"{cfg['api_base']}/sys/login3",
        json={"username": cfg["username"], "password": cfg["password"]},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 200 or not data.get("result", {}).get("token"):
        raise RuntimeError(f"登录失败: {data}")
    token = data["result"]["token"]
    session.headers.update({"X-Access-Token": token})
    print(f"[auth] 登录成功，用户: {cfg['username']}")


# ── 枚举查找 ──────────────────────────────────────────────

def _find_id(items: list, name: str, name_key: str, id_key: str) -> str:
    for item in items:
        if item.get(name_key) == name:
            return item[id_key]
    available = [item.get(name_key) for item in items]
    raise ValueError(f"找不到 '{name}'，可用值: {available}")


def resolve_ids(session: requests.Session, cfg: dict) -> dict:
    print("[resolve] 获取枚举数据...")
    base = cfg["api_base"]

    depts = session.get(f"{base}/master/buTaProduct/st-bu-list", params={"validOnly": 1}, timeout=15).json().get("result", [])
    dept_id = _find_id(depts, cfg["department"], "buNameCn", "bu")

    tas = session.get(f"{base}/master/buTaProduct/st-ta-list", params={"validOnly": 1}, timeout=15).json().get("result", [])
    ta_id = _find_id(tas, cfg["therapy_area"], "taNameCn", "ta")

    products = session.get(f"{base}/master/buTaProduct/st-product-list", params={"validOnly": 1, "ta": ta_id}, timeout=15).json().get("result", [])
    product_ids = [_find_id(products, p, "prodName", "prodCode") for p in cfg["products"]]

    provinces = session.post(f"{base}/master/city/province-list", json={}, timeout=15).json().get("result", [])
    province_id = _find_id(provinces, cfg["province"], "name", "id")

    cities = session.post(f"{base}/master/city/city-list", json={"provinceId": province_id}, timeout=15).json().get("result", [])
    city_id = _find_id(cities, cfg["city"], "name", "id")

    print(f"[resolve] dept={dept_id}, ta={ta_id}, products={product_ids}, province={province_id}, city={city_id}")
    return {"dept_id": dept_id, "ta_id": ta_id, "product_ids": product_ids, "province_id": province_id, "city_id": city_id}


# ── 创建/提交/验证 ─────────────────────────────────────────

def create_meeting(session: requests.Session, cfg: dict, ids: dict):
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

    resp = session.post(f"{cfg['api_base']}/planning/meeting/newCreate", json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"创建会议失败: {data}")
    meeting_id = data.get("result") or data.get("message")
    print(f"[create] 会议创建成功，id={meeting_id}")
    return meeting_id, year, season


def submit_meeting(session: requests.Session, cfg: dict, meeting_id: str, year: str, season: str) -> None:
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
        raise AssertionError(f"会议 {meeting_id} 未出现在审批中列表，当前列表 id: {ids}")
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


def main():
    parser = argparse.ArgumentParser(description="执行 Gmeeting 添加会议全流程")
    parser.add_argument("--session-id", required=True, help="由 write_session 生成的 session ID")
    args = parser.parse_args()

    try:
        cfg = read_csv(args.session_id)
    except FileNotFoundError as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[config] 从 CSV 加载配置，session_id={args.session_id}")

    try:
        meeting_id = run(cfg)
        print(f"[result] meeting_id={meeting_id}")
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


from langchain.tools import tool


@tool("run_meeting", parse_docstring=True)
def run_meeting_tool(session_id: str) -> str:
    """读取 session CSV，执行完整会议创建流程：登录→枚举解析→创建→提交→验证，返回 meeting_id。

    Args:
        session_id: 由 write_session 工具生成的 session ID。
    """
    try:
        cfg = read_csv(session_id)
    except FileNotFoundError as e:
        return f"[error] {e}"

    try:
        meeting_id = run(cfg)
        return json.dumps({"meeting_id": meeting_id, "session_id": session_id}, ensure_ascii=False)
    except Exception as e:
        return f"[error] {e}"
