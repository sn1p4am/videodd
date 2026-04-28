import json
from http.cookies import SimpleCookie
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BILIBILI_QR_GENERATE_URL = (
    "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
)
BILIBILI_QR_POLL_URL = (
    "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
)
BILIBILI_BUVID_URL = "https://api.bilibili.com/x/frontend/finger/spi"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
POLL_CODE_SUCCESS = 0
POLL_CODE_EXPIRED = 86038
POLL_CODE_NOT_CONFIRMED = 86090
POLL_CODE_NOT_SCANNED = 86101


def generate_qr(user_agent: str = "") -> dict:
    data = _request_json(
        BILIBILI_QR_GENERATE_URL,
        query={"source": "main-fe-header"},
        user_agent=user_agent,
    )
    if data.get("code") != 0:
        raise RuntimeError(data.get("message") or "生成 B 站登录二维码失败")

    qr_data = data.get("data") or {}
    url = qr_data.get("url")
    key = qr_data.get("qrcode_key")
    if not url or not key:
        raise RuntimeError("B 站登录二维码响应不完整")

    return {
        "url": url,
        "key": key,
        "qr_svg": _make_qr_svg(url),
        "status": "waiting",
        "message": "等待扫码",
    }


def poll_qr(key: str, user_agent: str = "") -> dict:
    key = key.strip()
    if not key:
        raise ValueError("二维码 key 不能为空")

    with _open(
        BILIBILI_QR_POLL_URL,
        query={"qrcode_key": key, "source": "main-fe-header"},
        user_agent=user_agent,
    ) as response:
        payload = _read_json_response(response)
        set_cookie_headers = response.headers.get_all("Set-Cookie") or []

    if payload.get("code") != 0:
        return {
            "status": "error",
            "code": int(payload.get("code") or -1),
            "message": payload.get("message") or "B 站登录状态查询失败",
        }

    data = payload.get("data") or {}
    code = int(data.get("code") or 0)
    message = data.get("message") or _poll_message(code)
    result = {
        "status": _poll_status(code),
        "code": code,
        "message": message,
        "cookies_text": "",
    }

    if code == POLL_CODE_SUCCESS:
        result["cookies_text"] = _build_cookie_header(set_cookie_headers, user_agent)
        result["message"] = "扫码登录成功"

    return result


def _open(url: str, *, query: dict[str, str], user_agent: str):
    full_url = f"{url}?{urlencode(query)}"
    request = Request(full_url, headers=_headers(user_agent))
    return urlopen(request, timeout=15)


def _request_json(url: str, *, query: dict[str, str], user_agent: str) -> dict:
    with _open(url, query=query, user_agent=user_agent) as response:
        return _read_json_response(response)


def _read_json_response(response) -> dict:
    raw = response.read().decode("utf-8")
    return json.loads(raw)


def _make_qr_svg(data: str) -> str:
    import qrcode
    import qrcode.image.svg

    image = qrcode.make(
        data,
        image_factory=qrcode.image.svg.SvgPathImage,
        box_size=6,
        border=2,
    )
    return image.to_string(encoding="unicode")


def _headers(user_agent: str) -> dict[str, str]:
    return {
        "User-Agent": user_agent or DEFAULT_USER_AGENT,
        "Origin": "https://www.bilibili.com",
        "Referer": "https://www.bilibili.com/",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }


def _poll_status(code: int) -> str:
    if code == POLL_CODE_SUCCESS:
        return "success"
    if code == POLL_CODE_EXPIRED:
        return "expired"
    if code == POLL_CODE_NOT_CONFIRMED:
        return "scanned"
    if code == POLL_CODE_NOT_SCANNED:
        return "waiting"
    return "error"


def _poll_message(code: int) -> str:
    messages = {
        POLL_CODE_SUCCESS: "扫码登录成功",
        POLL_CODE_EXPIRED: "二维码已过期",
        POLL_CODE_NOT_CONFIRMED: "已扫码，等待确认",
        POLL_CODE_NOT_SCANNED: "等待扫码",
    }
    return messages.get(code, "B 站登录状态异常")


def _build_cookie_header(set_cookie_headers: list[str], user_agent: str) -> str:
    cookies = SimpleCookie()
    buvid3 = _get_buvid3(user_agent)
    if buvid3:
        cookies["buvid3"] = buvid3

    for header in set_cookie_headers:
        parsed = SimpleCookie()
        parsed.load(header)
        for name, morsel in parsed.items():
            if name != "i-wanna-go-back":
                cookies[name] = morsel.value

    if "SESSDATA" not in cookies:
        raise RuntimeError("B 站登录成功，但响应中没有 SESSDATA")

    return "; ".join(f"{name}={morsel.value}" for name, morsel in cookies.items())


def _get_buvid3(user_agent: str) -> str:
    try:
        data = _request_json(BILIBILI_BUVID_URL, query={}, user_agent=user_agent)
    except Exception:
        return ""
    payload = data.get("data") or {}
    return payload.get("b_3") or ""
