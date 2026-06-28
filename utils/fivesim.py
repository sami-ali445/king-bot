"""
King Bot - 5sim API Integration
Virtual Numbers via 5sim service
"""

import requests
import logging
from config import FIVE_SIM_API_KEY, FIVE_SIM_BASE_URL

logger = logging.getLogger(__name__)

# Countries by price tier
COUNTRIES = {
    "tier1": {
        "price": 10,
        "name": "💎 الفئة الأولى ($10)",
        "countries": {
            "sa": "🇸🇦 السعودية",
            "ae": "🇦🇪 الإمارات",
            "kw": "🇰🇼 الكويت",
            "qa": "🇶🇦 قطر"
        }
    },
    "tier2": {
        "price": 7,
        "name": "🥈 الفئة الثانية ($7)",
        "countries": {
            "eg": "🇪🇬 مصر",
            "iq": "🇮🇶 العراق",
            "jo": "🇯🇴 الأردن",
            "tr": "🇹🇷 تركيا"
        }
    },
    "tier3": {
        "price": 5,
        "name": "🥉 الفئة الثالثة ($5)",
        "countries": {
            "th": "🇹🇭 تايلاند",
            "us": "🇺🇸 أمريكا",
            "gb": "🇬🇧 بريطانيا",
            "id": "🇮🇩 إندونيسيا",
            "ru": "🇷🇺 روسيا"
        }
    }
}


def get_headers():
    return {
        "Authorization": f"Bearer {FIVE_SIM_API_KEY}",
        "Content-Type": "application/json"
    }


def get_balance() -> float:
    """Get 5sim account balance"""
    try:
        resp = requests.get(f"{FIVE_SIM_BASE_URL}/user/profile", headers=get_headers(), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("balance", 0)
    except Exception as e:
        logger.error(f"5sim balance check failed: {e}")
    return None


def buy_number(country_code: str, service: str = "any") -> dict:
    """Buy a virtual number"""
    try:
        resp = requests.get(
            f"{FIVE_SIM_BASE_URL}/user/buy/activation/{service}/any/{country_code}",
            headers=get_headers(),
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "success": True,
                "id": data.get("id"),
                "phone": data.get("phone"),
                "price": data.get("price"),
                "country": data.get("country"),
                "product": data.get("product")
            }
        else:
            return {"success": False, "error": resp.text}
    except Exception as e:
        logger.error(f"5sim buy number failed: {e}")
        return {"success": False, "error": str(e)}


def check_sms(order_id: int) -> dict:
    """Check for SMS on a purchased number"""
    try:
        resp = requests.get(
            f"{FIVE_SIM_BASE_URL}/user/check/{order_id}",
            headers=get_headers(),
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            sms_list = data.get("sms", [])
            if sms_list:
                return {
                    "success": True,
                    "code": sms_list[0].get("code"),
                    "text": sms_list[0].get("text"),
                    "date": sms_list[0].get("date")
                }
            return {"success": False, "error": "لا يوجد رسالة بعد"}
        return {"success": False, "error": resp.text}
    except Exception as e:
        logger.error(f"5sim SMS check failed: {e}")
        return {"success": False, "error": str(e)}


def cancel_number(order_id: int) -> bool:
    """Cancel an order and get refund"""
    try:
        resp = requests.get(
            f"{FIVE_SIM_BASE_URL}/user/cancel/{order_id}",
            headers=get_headers(),
            timeout=10
        )
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"5sim cancel failed: {e}")
        return False


def finish_order(order_id: int) -> bool:
    """Mark order as finished (SMS received)"""
    try:
        resp = requests.get(
            f"{FIVE_SIM_BASE_URL}/user/finish/{order_id}",
            headers=get_headers(),
            timeout=10
        )
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"5sim finish failed: {e}")
        return False
