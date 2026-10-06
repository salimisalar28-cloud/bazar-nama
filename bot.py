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
    if value is None:
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


# ============================================================
# PERSIAN NUMBER FORMAT
# ============================================================

def to_persian_digits(text):
    translation = str.maketrans(
        "0123456789",
        "۰۱۲۳۴۵۶۷۸۹"
    )

    return str(text).translate(translation)


def format_number(value, decimals=0):
    number = to_decimal(value)

    if number is None:
        return "—"

    text = f"{number:,.{decimals}f}"

    if decimals > 0:
        text = text.rstrip("0").rstrip(".")

    text = text.replace(",", "٬")

    return to_persian_digits(text)


def format_toman_from_rial(value):
    number = to_decimal(value)

    if number is None:
        return "—"

    # IMPORTANT:
    # Rial -> Toman conversion
    toman_value = number / Decimal("10")

    return format_number(toman_value, 0)


def format_usd(value):
    number = to_decimal(value)

    if number is None:
        return "—"

    return format_number(number, 0)


# ============================================================
# GREGORIAN -> JALALI
# ============================================================

def gregorian_to_jalali(gy, gm, gd):

    g_days_in_month = [
        31, 28, 31, 30, 31, 30,
        31, 31, 30, 31, 30, 31
    ]

    j_days_in_month = [
        31, 31, 31, 31, 31, 31,
        30, 30, 30, 30, 30, 29
    ]

    gy2 = gy - 1600
    gm2 = gm - 1
    gd2 = gd - 1

    g_day_no = (
        365 * gy2
        + (gy2 + 3) // 4
        - (gy2 + 99) // 100
        + (gy2 + 399) // 400
    )

    for i in range(gm2):
        g_day_no += g_days_in_month[i]

    if (
        gm2 > 1
        and (
            (gy % 4 == 0 and gy % 100 != 0)
            or gy % 400 == 0
        )
    ):
        g_day_no += 1

    g_day_no += gd2

    j_day_no = g_day_no - 79

    j_np = j_day_no // 12053
    j_day_no %= 12053

    jy = (
        979
        + 33 * j_np
        + 4 * (j_day_no // 1461)
    )

    j_day_no %= 1461

    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365

    i = 0

    while (
        i < 11
        and j_day_no >= j_days_in_month[i]
    ):
        j_day_no -= j_days_in_month[i]
        i += 1

    jm = i + 1
    jd = j_day_no + 1

    return jy, jm, jd


def get_persian_datetime():

    now = datetime.now(
        ZoneInfo(TIMEZONE)
    )

    jy, jm, jd = gregorian_to_jalali(
        now.year,
        now.month,
        now.day
    )

    date_text = (
        f"{jy:04d}/{jm:02d}/{jd:02d}"
    )

    time_text = now.strftime("%H:%M")

    return (
        to_persian_digits(date_text),
        to_persian_digits(time_text)
    )


# ============================================================
# SERVIX
# ============================================================

def find_asset(data, code):
    for item in data:
        if item.get("code") == code:
            return item

    return None


def get_asset_value(data, code):
    asset = find_asset(data, code)

    if asset is None:
        return None

    return asset.get("value")


def get_prices():

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

    validate_required_assets(data)

    usd = get_asset_value(
        data,
        ASSET_CODES["usd"]
    )

    eur = get_asset_value(
        data,
        ASSET_CODES["eur"]
    )

    gold18 = get_asset_value(
        data,
        ASSET_CODES["gold18"]
    )

    gold24 = get_asset_value(
        data,
        ASSET_CODES["gold24"]
    )

    gold_ounce = get_asset_value(
        data,
        ASSET_CODES["gold_ounce"]
    )

    emami = get_asset_value(
        data,
        ASSET_CODES["emami"]
    )

    half = get_asset_value(
        data,
        ASSET_CODES["half"]
    )

    quarter = get_asset_value(
        data,
        ASSET_CODES["quarter"]
    )

    bahar = get_asset_value(
        data,
        ASSET_CODES["bahar"]
    )

    gerami = get_asset_value(
        data,
        ASSET_CODES["gerami"]
    )

    silver_ounce = get_asset_value(
        data,
        ASSET_CODES["silver_ounce"]
    )

    bitcoin = get_asset_value(
        data,
        ASSET_CODES["bitcoin"]
    )

    date_text, time_text = get_persian_datetime()

    report = (
        "<b>📊 بازارنما | Bazar Nama</b>\n"
        f"📅 {date_text} | ⏰ {time_text}\n"
        "\n"

        "<b>💵 ارز</b>\n"
        f"💵 دلار آزاد: <b>{format_toman_from_rial(usd)} تومان</b>\n"
        f"💶 یورو: <b>{format_toman_from_rial(eur)} تومان</b>\n"
        "\n"

        "<b>🥇 طلا</b>\n"
        f"🟡 طلای ۱۸ عیار: <b>{format_toman_from_rial(gold18)} تومان</b>\n"
        f"🟡 طلای ۲۴ عیار: <b>{format_toman_from_rial(gold24)} تومان</b>\n"
        f"🌎 اونس طلا: <b>${format_usd(gold_ounce)}</b>\n"
        "\n"

        "<b>🪙 سکه</b>\n"
        f"🔴 سکه امامی: <b>{format_toman_from_rial(emami)} تومان</b>\n"
        f"🟠 نیم‌سکه: <b>{format_toman_from_rial(half)} تومان</b>\n"
        f"🟠 ربع‌سکه: <b>{format_toman_from_rial(quarter)} تومان</b>\n"
        f"🟡 بهار آزادی: <b>{format_toman_from_rial(bahar)} تومان</b>\n"
        f"🟡 سکه گرمی: <b>{format_toman_from_rial(gerami)} تومان</b>\n"
        "\n"

        "<b>🥈 نقره</b>\n"
        f"🥈 اونس نقره: <b>${format_usd(silver_ounce)}</b>\n"
        "\n"

        "<b>₿ ارز دیجیتال</b>\n"
        f"₿ بیت‌کوین: <b>${format_usd(bitcoin)}</b>\n"
        "\n"

        "🔗 <b>@BazarNamaOfficial</b>"
    )

    return report


# ============================================================
# TELEGRAM
# ============================================================

def send_to_telegram(message):

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
