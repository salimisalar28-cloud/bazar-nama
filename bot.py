import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

SERVIX_API_KEY = os.environ["SERVIX_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SERVIX_URL = "https://servix.cc/api/v1/assets"


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


def toman(value):
    if value is None:
        return None
    return value / 10


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


def find_asset(data, code):
    for item in data:
        if item.get("code") == code:
            return item
    return None


def get_value(data, code):
    asset = find_asset(data, code)

    if asset is None:
        return None

    return asset.get("value")


def create_report(data):

    usd = get_value(data, "USD_RLS")
    eur = get_value(data, "EUR_RLS")

    gold18 = get_value(data, "GOLD_18_RLS")
    gold24 = get_value(data, "GOLD_24_RLS")
    gold_ounce = get_value(data, "GOLD_OUNCE_USD")

    emami = get_value(data, "SEKKEH_RLS")
    half = get_value(data, "NIM_SEKKEH_RLS")
    quarter = get_value(data, "ROB_SEKKEH_RLS")
    bahar = get_value(data, "BAHAR_RLS")
    gerami = get_value(data, "GERAMI_SEKKEH_RLS")

    silver_ounce = get_value(data, "SILVER_OUNCE_USD")

    btc = get_value(data, "BTC_USD")

    now = datetime.now(ZoneInfo("Asia/Tehran"))

    date_text = now.strftime("%Y/%m/%d")
    time_text = now.strftime("%H:%M")

    report = (
        "<b>📊 بازارنما | Bazar Nama</b>\n"
        "\n"
        "🕐 <b>گزارش بازار</b>\n"
        f"📅 {date_text}\n"
        f"⏰ {time_text}\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        "<b>💵 ارز</b>\n"
        "\n"
        f"💵 دلار:\n<b>{format_toman(usd)} تومان</b>\n"
        "\n"
        f"💶 یورو:\n<b>{format_toman(eur)} تومان</b>\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        "<b>🥇 طلا</b>\n"
        "\n"
        f"🟡 طلای ۱۸ عیار:\n<b>{format_toman(gold18)} تومان</b>\n"
        "\n"
        f"🟡 طلای ۲۴ عیار:\n<b>{format_toman(gold24)} تومان</b>\n"
        "\n"
        f"🌎 اونس طلا:\n<b>${format_usd(gold_ounce)}</b>\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        "<b>🪙 سکه</b>\n"
        "\n"
        f"🔴 سکه امامی:\n<b>{format_toman(emami)} تومان</b>\n"
        "\n"
        f"🟠 نیم‌سکه:\n<b>{format_toman(half)} تومان</b>\n"
        "\n"
        f"🟠 ربع‌سکه:\n<b>{format_toman(quarter)} تومان</b>\n"
        "\n"
        f"🟡 بهار آزادی:\n<b>{format_toman(bahar)} تومان</b>\n"
        "\n"
        f"🟡 سکه گرمی:\n<b>{format_toman(gerami)} تومان</b>\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        "<b>🥈 نقره</b>\n"
        "\n"
        f"🥈 اونس نقره:\n<b>${format_usd(silver_ounce)}</b>\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        "<b>₿ ارزهای دیجیتال</b>\n"
        "\n"
        f"₿ بیت‌کوین:\n<b>${format_usd(btc)}</b>\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        "📡 <b>منبع داده: Servix</b>\n"
        "🤖 <b>Bazar Nama | بازارنما</b>"
    )

    return report


def send_to_telegram(message):

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    response = requests.post(
        url,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise Exception(f"Telegram error: {result}")


def main():

    print("دریافت قیمت‌ها از Servix...")

    data = get_prices()

    print(
        "تعداد دارایی‌های دریافت‌شده:",
        len(data)
    )

    report = create_report(data)

    print("ارسال گزارش به
