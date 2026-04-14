"""
Gmeeting UAT 登录认证
持久化会话 cookies，便于多次执行脚本时复用已登录状态
"""
import json
import os
import requests
from config import DEFAULT_CONFIG

_COOKIE_FILE = "gmeeting_session.json"


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


def login(session: requests.Session, config: dict = None) -> dict:
    """
    登录 Gmeeting UAT，返回用户信息。
    session 会自动保存 cookie，后续请求复用即可。
    """
    cfg = config or DEFAULT_CONFIG
    session.headers.update(_HEADERS)
    resp = session.post(
        f"{cfg['api_base']}/sys/login3",
        json={"username": cfg["username"], "password": cfg["password"]},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    # API 返回格式: {code: 200, result: {token: ..., userInfo: ...}}
    if data.get("code") != 200 or not data.get("result", {}).get("token"):
        raise RuntimeError(f"登录失败: {data}")
    token = data["result"]["token"]
    session.headers.update({"X-Access-Token": token})
    print(f"[auth] 登录成功，用户: {cfg['username']}")
    save_session_cookies(session, _COOKIE_FILE)
    return data.get("result", {})


def load_session_cookies(session: requests.Session, path: str = _COOKIE_FILE) -> None:
    """从本地文件加载 cookie 到 session"""
    if not os.path.exists(path):
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for ck in data.get("cookies", []):
            name = ck.get("name")
            value = ck.get("value")
            if name:
                session.cookies.set(name, value)
    except Exception:
        # 若加载失败，忽略，继续走正常登录流程
        pass


def save_session_cookies(session: requests.Session, path: str = _COOKIE_FILE) -> None:
    """将当前 session 的 cookies 保存到本地文件"""
    cookies = [{"name": k, "value": v} for k, v in session.cookies.items()]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"cookies": cookies}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    s = requests.Session()
    load_session_cookies(s, _COOKIE_FILE)
    login(s)
