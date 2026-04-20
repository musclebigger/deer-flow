"""
write_session — 将用户确认的字段值写入 CSV，输出 session_id

用法：
    python -m tools.write_session --json '{"province": "安徽", "city": "合肥"}'
    python tools/write_session --json '...'

输出（stdout，两行）：
    <session_id>
    <csv_path>
"""
import argparse
import csv
import json
import os
import sys
import uuid

from langchain.tools import tool

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
    ("meeting_name",    "会议名称"),
    ("department",      "业务部门"),
    ("therapy_area",    "治疗领域"),
    ("products",        "产品名称"),
    ("meeting_type",    "会议类别"),
    ("meeting_format",  "会议形式"),
    ("location_type",   "单点会/多点会"),
    ("venue_type",      "举办地类别"),
    ("start_month",     "开始年月"),
    ("province",        "省/直辖市"),
    ("city",            "城市"),
    ("speakers_total",   "计划讲者人数"),
    ("speakers_offline", "计划讲者人数（线下）"),
    ("attendees_total",  "计划参会者人数"),
    ("attendees_offline","计划参会者人数（线下）"),
    ("total_budget",     "总预算"),
    ("brand_budgets",    "品牌预算"),
]

_TMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "temp")


def new_session_id() -> str:
    return uuid.uuid4().hex[:12]


def write_csv(session_id: str, cfg: dict) -> str:
    os.makedirs(_TMP_DIR, exist_ok=True)
    path = os.path.join(_TMP_DIR, f"gmeeting_{session_id}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["field", "value"])
        for key, _ in FIELDS:
            val = cfg.get(key, "")
            if isinstance(val, list):
                val = ",".join(str(v) for v in val)
            elif isinstance(val, dict):
                val = ",".join(f"{k}:{v}" for k, v in val.items())
            writer.writerow([key, val])
    return path


def main():
    parser = argparse.ArgumentParser(description="写入会议表单 session CSV")
    parser.add_argument("--json", required=True, help="用户确认的字段值 JSON（只需传入与默认值不同的字段）")
    args = parser.parse_args()

    try:
        overrides = json.loads(args.json)
    except json.JSONDecodeError as e:
        print(f"[error] JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(1)

    cfg = dict(DEFAULT_CONFIG)
    for key, val in overrides.items():
        if key in cfg:
            cfg[key] = val

    sid = new_session_id()
    path = write_csv(sid, cfg)
    print(sid)
    print(path)


if __name__ == "__main__":
    main()


@tool("write_session", parse_docstring=True)
def write_session_tool(fields_json: str) -> str:
    """将用户确认的会议表单字段写入 CSV，返回 session_id 和文件路径。

    Args:
        fields_json: 用户确认的字段值 JSON 字符串，只需传入与默认值不同的字段，如 '{"province": "安徽", "city": "合肥"}'。
    """
    try:
        overrides = json.loads(fields_json)
    except json.JSONDecodeError as e:
        return f"[error] JSON 解析失败: {e}"

    cfg = dict(DEFAULT_CONFIG)
    for key, val in overrides.items():
        if key in cfg:
            cfg[key] = val

    sid = new_session_id()
    path = write_csv(sid, cfg)
    return json.dumps({"session_id": sid, "csv_path": path}, ensure_ascii=False)

