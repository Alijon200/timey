import os
import requests
from functools import lru_cache

ESKIZ_BASE = "https://notify.eskiz.uz/api"

class EskizError(Exception):
    pass



def _find_jwt(obj):
    """JSON ichidan JWTga o‘xshagan tokenni topadi (aaa.bbb.ccc)."""
    if isinstance(obj, dict):
        for v in obj.values():
            t = _find_jwt(v)
            if t:
                return t
    elif isinstance(obj, list):
        for it in obj:
            t = _find_jwt(it)
            if t:
                return t
    elif isinstance(obj, str):
        s = obj.strip()
        if s.count(".") == 2:  # JWT belgisi
            return s
    return None


@lru_cache(maxsize=1)
def eskiz_get_token() -> str:

    email = os.getenv("ESKIZ_EMAIL")
    secret = os.getenv("ESKIZ_SECRET_KEY")  # Eskiz: password = secret key :contentReference[oaicite:1]{index=1}

    if not email or not secret:
        raise EskizError("ESKIZ_EMAIL yoki ESKIZ_SECRET_KEY env'da yo‘q")
    r = requests.post(
        f"{ESKIZ_BASE}/auth/login",
        data={"email": email, "password": secret},
        timeout=20,
    )
    
    if r.status_code != 200:
        raise EskizError(f"Eskiz login error {r.status_code}: {r.text}")

    try:
        payload = r.json()
    except Exception:
        raise EskizError(f"Eskiz login non-JSON: {r.text}")

    token = _find_jwt(payload)
    if not token:
        # JWT topilmasa, demak response boshqa formatda yoki login token bermayapti
        raise EskizError(f"JWT token topilmadi. Login response: {payload}")

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


