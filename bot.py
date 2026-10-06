import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

import requests


# ============================================================
# CONFIGURATION
# ============================================================

SERVIX_API_KEY = os.environ["SERVIX_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SERVIX_URL = "https://servix.cc/api/v1/assets"
TELEGRAM_URL = (
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
)

TIMEZONE = "Asia/Tehran"


# ============================================================
# ASSET CODES
# ============================================================

ASSET_CODES = {
    "usd": "USD_RLS",
    "eur": "EUR_RLS",

    "gold18": "GOLD_18_RLS",
    "gold24": "GOLD_24_RLS",
    "gold_ounce": "GOLD_OUNCE_USD",

    "emami": "SEKKEH_RLS",
    "half": "NIM_SEKKEH_RLS",
    "quarter": "ROB_SEKKEH_RLS",
    "bahar": "BAHAR_RLS",
    "gerami": "GERAMI_SEKKEH_RLS",

    "silver_ounce": "SILVER_OUNCE_USD",

    "bitcoin": "BTC_USD",
}


# ============================================================
# HELPERS
# ============================================================

def require_environment():
    """
    Verify that all required environment variables exist.
    Secrets themselves are never printed.
    """

    required = {
        "SERVIX_API_KEY": SERVIX_API_KEY,
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
    }

    missing = [
        name
        for name, value in required.items()
        if value is None or str(value).strip() == ""
    ]

    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )


def to_decimal(value):
    """
    Safely convert numeric API values to Decimal.
    """

    if value is None:
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def format_number(value, decimals=2):
    """
    Format a numeric value with thousands separators.
    """

    number = to_decimal(value)

    if number is None:
        return "—"

    if decimals == 0:
        return f"{number:,.0f}"

    text = f"{number:,.{decimals}f}"

    # Remove unnecessary trailing zeroes.
    text = text.rstrip("0").rstrip(".")

    return text


def format_toman_from_rial(value):
    """
    Servix RLS values are Iranian Rial.
    Convert Rial -> Toman by dividing by 10.
    """

    number = to_decimal(value)

    if number is None:
        return "—"

    toman_value = number / Decimal("10")

    return format_number(toman_value, 2)


def format_usd(value):
    """
    Format USD-based asset values.
    """

    number = to_decimal(value)

    if number is None:
        return "—"

    return format_number(number, 2)


def find_asset(data, code):
    """
    Find an asset by its Servix code.
    """

    for item in data:
        if item.get("code") == code:
            return item

    return None


def get_asset_value(data, code):
    """
    Return the current value of a specific asset.
    """

    asset = find_asset(data, code)

    if asset is None:
        return None

    return asset.get("value")


# ============================================================
# SERVIX
# ============================================================

def get_prices():
    """
    Get the latest complete asset list from Servix.
    """

    headers = {
        "X-API-Key": SERVIX_API_KEY,
        "Accept": "application/json",
    }

    try:
        response = requests.get(
            SERVIX_URL,
            headers=headers,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not connect to Servix: {exc}"
        ) from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"Servix returned HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Servix returned invalid JSON."
        ) from exc

    if not isinstance(data, list):
        raise RuntimeError(
            "Unexpected Servix response format. "
            "Expected a list of assets."
        )

    if len(data) == 0:
        raise RuntimeError(
            "Servix returned an empty asset list."
        )

    return data


def validate_required_assets(data):
    """
    Check that every asset required by the report exists.
    """

    missing = []

    for code in ASSET_CODES.values():
        if find_asset(data, code) is None:
            missing.append(code)

    if missing:
        raise RuntimeError(
            "The following required Servix assets were not found: "
            + ", ".join(missing)
        )


# ============================================================
# REPORT
# ============================================================

def create_report(data):
    """
    Build the Telegram market report.
    """

    validate_required_assets(data)

    usd = get_asset_value(data, ASSET_CODES["usd"])
    eur = get_asset_value(data, ASSET_CODES["eur"])

    gold18 = get_asset_value(data, ASSET_CODES["gold18"])
    gold24 = get_asset_value(data, ASSET_CODES["gold24"])
    gold_ounce = get_asset_value(data, ASSET_CODES["gold_ounce"])

    emami = get_asset_value(data, ASSET_CODES["emami"])
    half = get_asset_value(data, ASSET_CODES["half"])
    quarter = get_asset_value(data, ASSET_CODES["quarter"])
    bahar = get_asset_value(data, ASSET_CODES["bahar"])
    gerami = get_asset_value(data, ASSET_CODES["gerami"])

    silver_ounce = get_asset_value(
        data,
        ASSET_CODES["silver_ounce"]
    )

    bitcoin = get_asset_value(
        data,
        ASSET_CODES["bitcoin"]
    )

    now = datetime.now(
        ZoneInfo(TIMEZONE)
    )

    date_text = now.strftime("%Y/%m/%d")
    time_text = now.strftime("%H:%M")

    report = (
        "<b>📊 بازارنما | Bazar Nama</b>\n"
        "\n"
        f"📅 تاریخ: <b>{date_text}</b>\n"
        f"⏰ ساعت: <b>{time_text}</b>\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        "<b>💵 ارز</b>\n"
        "\n"
        f"💵 دلار آزاد:\n"
        f"<b>{format_toman_from_rial(usd)} تومان</b>\n"
        "\n"
        f"💶 یورو:\n"
        f"<b>{format_toman_from_rial(eur)} تومان</b>\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        "<b>🥇 طلا</b>\n"
        "\n"
        f"🟡 طلای ۱۸ عیار:\n"
        f"<b>{format_toman_from_rial(gold18)} تومان</b>\n"
        "\n"
        f"🟡 طلای ۲۴ عیار:\n"
        f"<b>{format_toman_from_rial(gold24)} تومان</b>\n"
        "\n"
        f"🌎 اونس طلا:\n"
        f"<b>${format_usd(gold_ounce)}</b>\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        "<b>🪙 سکه</b>\n"
        "\n"
        f"🔴 سکه امامی:\n"
        f"<b>{format_toman_from_rial(emami)} تومان</b>\n"
        "\n"
        f"🟠 نیم‌سکه:\n"
        f"<b>{format_toman_from_rial(half)} تومان</b>\n"
        "\n"
        f"🟠 ربع‌سکه:\n"
        f"<b>{format_toman_from_rial(quarter)} تومان</b>\n"
        "\n"
        f"🟡 بهار آزادی:\n"
        f"<b>{format_toman_from_rial(bahar)} تومان</b>\n"
        "\n"
        f"🟡 سکه گرمی:\n"
        f"<b>{format_toman_from_rial(gerami)} تومان</b>\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        "<b>🥈 نقره</b>\n"
        "\n"
        f"🥈 اونس نقره:\n"
        f"<b>${format_usd(silver_ounce)}</b>\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        "<b>₿ ارز دیجیتال</b>\n"
        "\n"
        f"₿ بیت‌کوین:\n"
        f"<b>${format_usd(bitcoin)}</b>\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        "📡 <b>منبع داده: Servix</b>\n"
        "🤖 <b>Bazar Nama | بازارنما</b>"
    )

    return report


# ============================================================
# TELEGRAM
# ============================================================

def send_to_telegram(message):
    """
    Send the generated report to Telegram.
    """

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(
            TELEGRAM_URL,
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not connect to Telegram: {exc}"
        ) from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"Telegram returned HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )

    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Telegram returned invalid JSON."
        ) from exc

    if not result.get("ok"):
        raise RuntimeError(
            f"Telegram API error: {result}"
        )

    return result


# ============================================================
# MAIN
# ============================================================

def main():
    print("========================================")
    print("Bazar Nama starting...")
    print("========================================")

    require_environment()

    print("1/4 - دریافت قیمت‌ها از Servix...")

    data = get_prices()

    print(
        f"    تعداد دارایی‌های دریافت‌شده: {len(data)}"
    )

    print("2/4 - بررسی دارایی‌های موردنیاز...")

    validate_required_assets(data)

    print("    همه دارایی‌های موردنیاز موجود هستند.")

    print("3/4 - ساخت گزارش...")

    report = create_report(data)

    print(
        f"    طول گزارش: {len(report)} کاراکتر"
    )

    print("4/4 - ارسال گزارش به Telegram...")

    send_to_telegram(report)

    print("========================================")
    print("گزارش با موفقیت ارسال شد.")
    print("========================================")


if __name__ == "__main__":
    main()
