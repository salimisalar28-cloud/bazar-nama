import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# تنظیمات
# =========================

SERVIX_API_KEY = os.environ["SERVIX_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SERVIX_URL = "https://servix.cc/api/v1/assets"

# =========================
# دریافت اطلاعات از Servix
# =========================

def get_prices():
    headers = {
        "X-API-Key": SERVIX_API_KEY
    }

    response = requests.get(
        SERVIX_URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()
    return response.json()


# =========================
# تبدیل ریال به تومان
# =========================

def toman(value):
    if value is None:
        return None

    return value / 10


# =========================
# فرمت قیمت
# =========================

def format_toman(value):
    if value is None:
        return "—"

    value = toman(value)

    if abs(value - round(value)) < 0.01:
        return f"{int(round(value)):,}"

    return f"{value:,.2f}"


def format_usd(value):
    if value is None:
        return "—"

    if abs(value - round(value)) < 0.01:
        return f"{int(round(value)):,}"

    return f"{value:,.2f}"


# =========================
# پیدا کردن دارایی
# =========================

def find_asset(data, code):
    for item in data:
        if item.get("code") == code:
            return item

    return None


# =========================
# ساخت گزارش
# =========================

def create_report(data):

    usd = find_asset(data, "USD_RLS")
    eur = find_asset(data, "EUR_RLS")

    gold18 = find_asset(data, "GOLD_18_RLS")
    gold24 = find_asset(data, "GOLD_24_RLS")

    emami = find_asset(data, "SEKKEH_RLS")
    half = find_asset(data, "NIM_SEKKEH_RLS")
    quarter = find_asset(data, "ROB_SEKKEH_RLS")
    bahar = find_asset(data, "BAHAR_RLS")
    gerami = find_asset(data, "GERAMI_SEKKEH_RLS")

    gold_ounce = find_asset(data, "GOLD_OUNCE_USD")
    silver_ounce = find_asset(data, "SILVER_OUNCE_USD")

    btc = find_asset(data, "BTC_USD")

    # زمان ایران
    now = datetime.now(ZoneInfo("Asia/Tehran"))

    date_text = now.strftime("%Y/%m/%d")
    time_text = now.strftime("%H:%M")

    report = f"""
<b>📊 بازارنما | Bazar Nama</b>

🕐 <b>گزارش بازار</b>
📅 {date_text}
⏰ {time_text}

━━━━━━━━━━━━━━

<b>💵 ارز</b>

💵 دلار:
<b>{format_toman(usd.get("value") if usd else None)} تومان</b>

💶 یورو:
<b>{format_toman(eur.get("value") if eur else None)} تومان</b>

━━━━━━━━━━━━━━

<b>🥇 طلا</b>

🟡 طلای ۱۸ عیار:
<b>{format_toman(gold18.get("value") if gold18 else None)} تومان</b>

🟡 طلای ۲۴ عیار:
<b>{format_toman(gold24.get("value") if gold24 else None)} تومان</b>

🌎 اونس طلا:
<b>${format_usd(gold_ounce.get("value") if gold_ounce else None)}</b>

━━━━━━━━━━━━━━

<b>🪙 سکه</b>

🔴 سکه امامی:
<b>{format_toman(emami.get("value") if emami else None)} تومان</b>

🟠 نیم‌سکه:
<b>{format_toman(half.get("value") if half else None)} تومان</b>

🟠 ربع‌سکه:
<b>{format_toman(quarter.get("value") if quarter else None)} تومان</
