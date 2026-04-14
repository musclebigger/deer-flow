"""
Gmeeting 表单 Session 管理
- 生成唯一 session ID
- 将用户确认的字段值写入 C:/tmp/gmeeting_<session_id>.csv
- 从 CSV 读取字段值供 add_meeting.py 使用
"""
import csv
import os
import uuid
from config import DEFAULT_CONFIG

_TMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp")

# 所有需要向用户确认的字段，顺序即询问顺序
FIELDS = [
    ("meeting_name",    "会议名称"),
    ("department",      "业务部门"),
    ("therapy_area",    "治疗领域"),
    ("products",        "产品名称（多个用逗号分隔）"),
    ("meeting_type",    "会议类别"),
    ("meeting_format",  "会议形式"),
    ("location_type",   "单点会/多点会"),
    ("venue_type",      "举办地类别"),
    ("start_month",     "开始年月（YYYY-MM）"),
    ("province",        "省/直辖市"),
    ("city",            "城市"),
    ("speakers_total",          "计划讲者人数"),
    ("speakers_offline",        "计划讲者人数（线下）"),
    ("attendees_total",         "计划参会者人数"),
    ("attendees_offline",       "计划参会者人数（线下）"),
    ("total_budget",            "总预算"),
    ("brand_budgets",           "品牌预算（格式：产品名:金额）"),
]


def new_session_id() -> str:
    return uuid.uuid4().hex[:12]


def csv_path(session_id: str) -> str:
    os.makedirs(_TMP_DIR, exist_ok=True)
    return os.path.join(_TMP_DIR, f"gmeeting_{session_id}.csv")


def write_csv(session_id: str, cfg: dict) -> str:
    """将 cfg 中的字段写入 CSV，返回文件路径"""
    path = csv_path(session_id)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["field", "value"])
        for key, _ in FIELDS:
            val = cfg.get(key, "")
            # list/dict 序列化为字符串
            if isinstance(val, list):
                val = ",".join(str(v) for v in val)
            elif isinstance(val, dict):
                val = ",".join(f"{k}:{v}" for k, v in val.items())
            writer.writerow([key, val])
    return path


def read_csv(session_id: str) -> dict:
    """从 CSV 读取字段值，返回 cfg dict（类型与 DEFAULT_CONFIG 对齐）"""
    path = csv_path(session_id)
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


def build_confirmation_table(cfg: dict) -> str:
    """生成给用户看的字段确认表格（Markdown）"""
    lines = ["| 字段 | 当前值 |", "|---|---|"]
    for key, label in FIELDS:
        val = cfg.get(key, "")
        if isinstance(val, list):
            val = ", ".join(str(v) for v in val)
        elif isinstance(val, dict):
            val = ", ".join(f"{k}: {v}" for k, v in val.items())
        lines.append(f"| {label} | {val} |")
    return "\n".join(lines)
