"""
Gmeeting UAT API 封装
所有表单操作通过 HTTP 请求完成，无需浏览器。
"""
import requests
from config import DEFAULT_CONFIG


def _base(config: dict) -> str:
    return config.get("api_base", DEFAULT_CONFIG["api_base"])


# ── 枚举数据 ──────────────────────────────────────────────

def get_departments(session: requests.Session, config: dict = None) -> list:
    """获取业务部门列表 — GET /master/buTaProduct/st-bu-list, result[].buNameCn / bu"""
    resp = session.get(
        f"{_base(config or DEFAULT_CONFIG)}/master/buTaProduct/st-bu-list",
        params={"validOnly": 1},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("result", [])


def get_therapy_areas(session: requests.Session, config: dict = None) -> list:
    """获取治疗领域列表 — GET /master/buTaProduct/st-ta-list, result[].taNameCn / ta"""
    resp = session.get(
        f"{_base(config or DEFAULT_CONFIG)}/master/buTaProduct/st-ta-list",
        params={"validOnly": 1},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("result", [])


def get_products(session: requests.Session, ta_code: str = None, config: dict = None) -> list:
    """获取产品列表 — GET /master/buTaProduct/st-product-list, result[].prodName / prodCode"""
    params = {"validOnly": 1}
    if ta_code:
        params["ta"] = ta_code
    resp = session.get(
        f"{_base(config or DEFAULT_CONFIG)}/master/buTaProduct/st-product-list",
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("result", [])


def get_provinces(session: requests.Session, config: dict = None) -> list:
    """获取省份列表 — POST /master/city/province-list, result[].name / id"""
    resp = session.post(
        f"{_base(config or DEFAULT_CONFIG)}/master/city/province-list",
        json={},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("result", [])


def get_cities(session: requests.Session, province_id: str, config: dict = None) -> list:
    """获取城市列表 — POST /master/city/city-list, result[].name / id"""
    resp = session.post(
        f"{_base(config or DEFAULT_CONFIG)}/master/city/city-list",
        json={"provinceId": province_id},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("result", [])


# ── 名称 → ID 解析工具 ────────────────────────────────────

def find_id(items: list, name: str, name_key: str = "name", id_key: str = "id", alt_name_keys: list = None) -> str:
    """从列表中按名称查找 ID，支持多个备选 name_key，找不到抛出 ValueError"""
    keys = [name_key] + (alt_name_keys or [])
    for item in items:
        for k in keys:
            if item.get(k) == name:
                return item[id_key]
    available = [item.get(name_key) for item in items]
    raise ValueError(f"找不到 '{name}'，可用值: {available}")


def find_code(items: list, name: str, name_key: str = "name", code_key: str = "code") -> str:
    """从列表中按名称查找 code"""
    return find_id(items, name, name_key=name_key, id_key=code_key)
