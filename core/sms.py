import os
import requests
from functools import lru_cache

ESKIZ_BASE = "https://notify.eskiz.uz/api"

class EskizError(Exception):
    pass


def mask(s: str, keep=6):
    if not s:
        return ""
    s = s.strip()
    if len(s) <= keep*2:
        return "*" * len(s)
    return s[:keep] + "*"*(len(s)-keep*2) + s[-keep:]

@lru_cache(maxsize=1)
def eskiz_get_token() -> str:
    
    email = os.getenv("ESKIZ_EMAIL")
    secret = os.getenv("ESKIZ_SECRET_KEY")

    print("ESKIZ_EMAIL =", email)
    print("ESKIZ_SECRET_KEY length =", len(secret or ""))

    if not email or not secret:
        raise EskizError("ESKIZ_EMAIL yoki ESKIZ_SECRET_KEY yo‘q")

    r = requests.post(
        f"{ESKIZ_BASE}/auth/login",
        data={"email": email, "password": secret},
        timeout=20,
    )

    print("LOGIN STATUS:", r.status_code)
    print("LOGIN TEXT:", r.text[:500])  # 500 ta belgi kifoya

    if r.status_code != 200:
        raise EskizError(f"Eskiz login error {r.status_code}: {r.text}")

    data = r.json()

    # eng ko‘p uchraydigan formatlar:
    token = (
        data.get("data", {}).get("token")
        or data.get("data", {}).get("access_token")
        or data.get("token")
        or data.get("access_token")
    )

    if not token:
        raise EskizError(f"Token topilmadi. Response: {data}")

    token = token.strip()
    print("TOKEN len:", len(token), "dots:", token.count("."), "masked:", mask(token))

    return token




def eskiz_send_sms(phone: str, text: str) -> dict:
    token = eskiz_get_token()

    sender = os.getenv("ESKIZ_SENDER", "4546")
    mobile_phone = phone.replace("+", "")

    r = requests.post(
        f"{ESKIZ_BASE}/message/sms/send",
        headers={"Authorization": f"Bearer {token}"},
        data={"mobile_phone": mobile_phone, "message": text, "from": sender},
        timeout=20,
    )

    # Debug:
    # print("SEND STATUS:", r.status_code)
    # print("SEND TEXT:", r.text)

    if r.status_code != 200:
        raise EskizError(f"Eskiz send error {r.status_code}: {r.text}")

    return r.json()

@lru_cache(maxsize=1)
def eskiz_get_token() -> str:
    email = os.getenv("ESKIZ_EMAIL")
    secret = os.getenv("ESKIZ_SECRET_KEY")

    print("ESKIZ_EMAIL =", email)
    print("ESKIZ_SECRET_KEY length =", len(secret or ""))

    ...


