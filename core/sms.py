import os
import requests
from functools import lru_cache

ESKIZ_BASE = "https://notify.eskiz.uz/api"

class EskizError(Exception):
    pass

@lru_cache(maxsize=1)
def eskiz_get_token() -> str:
    """
    Eskiz token olish.
    Ba'zi akkauntlarda 'secret_key' bilan token beriladi.
    """
    email = os.getenv("ESKIZ_EMAIL")
    secret = os.getenv("ESKIZ_SECRET_KEY")

    if not email or not secret:
        raise EskizError("ESKIZ_EMAIL yoki ESKIZ_SECRET_KEY .env da yo‘q")

    # ✅ Token olish (gateway)
    r = requests.post(
        f"{ESKIZ_BASE}/auth/login",
        data={"email": email, "password": secret},  # ko'pincha secret shu yerga beriladi
        timeout=20,
    )

    # Debug uchun:
    # print("TOKEN STATUS:", r.status_code)
    # print("TOKEN TEXT:", r.text)

    if r.status_code != 200:
        raise EskizError(f"Eskiz token error {r.status_code}: {r.text}")

    return r.json()["data"]["token"]


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
