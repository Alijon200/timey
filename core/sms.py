import os
import requests

ESKIZ_BASE = "https://notify.eskiz.uz/api"


class EskizError(Exception):
    pass


def eskiz_get_token() -> str:
    email = os.getenv("ESKIZ_EMAIL")
    secret = os.getenv("ESKIZ_SECRET_KEY")

    if not email or not secret:
        raise EskizError("ESKIZ_EMAIL yoki ESKIZ_SECRET_KEY yo‘q")

    r = requests.post(
        f"{ESKIZ_BASE}/auth/login",
        data={"email": email, "password": secret},
        timeout=20,
    )

    try:
        data = r.json()
    except Exception:
        raise EskizError(f"Eskiz login json emas. status={r.status_code}, text={r.text[:200]}")

    # ✅ Eskiz login ba'zan "status": "success" bermaydi.
    # Biz token bor-yo‘qligini tekshiramiz.
    token = (data.get("data") or {}).get("token")
    if r.status_code != 200 or not token:
        raise EskizError(f"Eskiz login error: status={r.status_code}, data={data}")

    return token


def eskiz_send_sms(phone: str, text: str) -> dict:
    """
    Hech qachon serverni yiqitmaydi:
    - sent=True/False qaytaradi
    - error/info qaytaradi
    """
    from django.conf import settings

    # DEV rejimda SMS yubormaymiz
    if getattr(settings, "DEV_OTP_MODE", False):
        return {"sent": False, "mode": "dev", "message": "DEV_OTP_MODE=1, SMS not sent"}

    try:
        token = eskiz_get_token()

        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "mobile_phone": phone.replace("+", ""),
            "message": text,
            "from": os.getenv("ESKIZ_FROM", "4546"),
        }

        r = requests.post(
            f"{ESKIZ_BASE}/message/sms/send",
            data=payload,
            headers=headers,
            timeout=20,
        )

        try:
            data = r.json()
        except Exception:
            data = {"raw_text": r.text[:500]}

        ok = (r.status_code == 200) and (data.get("status") == "success")
        return {"sent": ok, "status_code": r.status_code, "data": data}

    except Exception as e:
        # ✅ Eng muhim joy: exception tashlamaymiz
        return {"sent": False, "error": str(e)}
