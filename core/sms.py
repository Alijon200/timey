import os
import requests
from functools import lru_cache

ESKIZ_BASE = "https://notify.eskiz.uz/api"


class EskizError(Exception):
    pass


def mask(s: str, keep: int = 6) -> str:
    """Tokenni logda yashirib ko'rsatish uchun."""
    if not s:
        return ""
    s = s.strip()
    if len(s) <= keep * 2:
        return "*" * len(s)
    return s[:keep] + "*" * (len(s) - keep * 2) + s[-keep:]


def _env(name: str, default: str | None = None) -> str | None:
    """Env o'qish (bo'sh string bo'lsa ham None qiladi)."""
    v = os.getenv(name, default)
    if v is None:
        return None
    v = v.strip()
    return v if v else None


@lru_cache(maxsize=1)
def eskiz_get_token() -> str:
    """
    Eskiz'dan token olish.
    ESKIZ_SECRET_KEY — Eskiz kabinetdagi API password/secret (akkaunt paroli bo'lishi ham mumkin).
    """
    email = _env("ESKIZ_EMAIL")
    secret = _env("ESKIZ_SECRET_KEY")

    print("ESKIZ_EMAIL =", email)
    print("ESKIZ_SECRET_KEY length =", len(secret or ""))

    if not email or not secret:
        raise EskizError("ESKIZ_EMAIL yoki ESKIZ_SECRET_KEY env'da yo‘q")

    r = requests.post(
        f"{ESKIZ_BASE}/auth/login",
        data={"email": email, "password": secret},
        timeout=20,
    )

    print("LOGIN STATUS:", r.status_code)
    print("LOGIN TEXT:", r.text[:500])

    if r.status_code != 200:
        raise EskizError(f"Eskiz login error {r.status_code}: {r.text}")

    try:
        data = r.json()
    except Exception:
        raise EskizError(f"Eskiz login JSON emas: {r.text}")

    # Eskiz ko'pincha shu formatda qaytaradi: {"data":{"token":"..."}}
    token = (
        (data.get("data") or {}).get("token")
        or (data.get("data") or {}).get("access_token")
        or data.get("token")
        or data.get("access_token")
    )

    if not token:
        raise EskizError(f"Token topilmadi. Response: {data}")

    token = str(token).strip()
    print("TOKEN len:", len(token), "dots:", token.count("."), "masked:", mask(token))

    # JWT bo'lishi kerak: aaa.bbb.ccc
    if token.count(".") != 2:
        raise EskizError(
            f"Eskiz token JWT emas (dots={token.count('.')}). "
            f"Token masked: {mask(token)}"
        )

    return token


def eskiz_send_sms(phone: str, text: str) -> dict:
    token = eskiz_get_token()

    sender = _env("ESKIZ_SENDER") or "4546"
    mobile_phone = (phone or "").replace("+", "").strip()

    if not mobile_phone.isdigit():
        raise EskizError(f"Telefon formati noto‘g‘ri: {phone}")

    r = requests.post(
        f"{ESKIZ_BASE}/message/sms/send",
        headers={"Authorization": f"Bearer {token}"},
        data={"mobile_phone": mobile_phone, "message": text, "from": sender},
        timeout=20,
    )

    print("SEND STATUS:", r.status_code)
    print("SEND TEXT:", r.text[:500])

    if r.status_code != 200:
        raise EskizError(f"Eskiz send error {r.status_code}: {r.text}")

    try:
        return r.json()
    except Exception:
        return {"raw": r.text}
