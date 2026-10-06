import os
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

import requests


SERVIX_URL = "https://servix.cc/api/v1/assets"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SERVIX_API_KEY = os.getenv("SERVIX_API_KEY")


ASSET_CODES = {
    "usd": "USD_RLS",
    "eur": "EUR_RLS",
    "gold_18": "GOLD_18_RLS",
    "gold_24": "GOLD_24_RLS",
    "gold_ounce": "GOLD_OUNCE_USD",
    "sekkeh_emami": "SEKKEH_RLS",
    "nim_sekkeh": "NIM_SEKKEH_RLS",
    "rob_sekkeh": "ROB_SEKKEH_RLS",
    "bahar": "BAHAR_RLS",
    "gerami_sekkeh": "GERAMI_SEKKEH_RLS",
    "silver_ounce": "SILVER_OUNCE_USD",
    "bitcoin": "BTC_USD",
}


def to_decimal(value):
    return Decimal(str(value))


def format_number(value):
    """
    نمایش عدد:
    - بدون اعشار
    - گرد شده به نزدیک‌ترین عدد صحیح
    - با جداکننده هزارگان
    """
    number = to_decimal(value).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )

    formatted = f"{number:,}"

    # تبدیل جداکننده انگلیسی به جداکننده فارسی
    formatted = formatted.replace(",", "٬")

    # تبدیل اعداد انگلیسی به فارسی
    persian_digits = str.maketrans(
        "0123456789",
        "۰۱۲۳۴۵۶۷۸۹"
    )

    return formatted.translate(persian_digits)


def format_usd(value):
    return "$" + format_number(value)


def gregorian_to_jalali(gy, gm, gd):
    """
    تبدیل تاریخ میلادی به شمسی
    """
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

    if gm2 > 1 and (
        gy % 4 == 0
        and (gy % 100 != 0 or gy % 400 == 0)
    ):
        g_day_no += 1

    g_day_no += gd2

    j_day_no = g_day_no - 79

    j_np = j_day_no // 12053
    j_day_no %= 12053

    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
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


def get_jalali_date():
    iran_time = datetime.now(
        ZoneInfo("Asia/Tehran")
    )

    jy, jm, jd = gregorian_to_jalali(
        iran_time.year,
        iran_time.month,
        iran_time.day
    )

    return (
        f"{jy:04d}/{jm:02d}/{jd:02d}"
    ).translate(
        str.maketrans(
            "0123456789",
            "۰۱۲۳۴۵۶۷۸۹"
        )
    )


def get_iran_time():
    return datetime.now(
        ZoneInfo("Asia/Tehran")
    )


def get_prices():
    if not SERVIX_API_KEY:
        raise RuntimeError(
            "SERVIX_API_KEY is not configured."
        )

    response = requests.get(
        SERVIX_URL,
        headers={
            "X-API-Key": SERVIX_API_KEY
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if isinstance(data, dict):
        assets = data.get("data", data.get("assets", data))
    else:
        assets = data

    if not isinstance(assets, list):
        raise RuntimeError(
            "Unexpected Servix API response format."
        )

    prices = {}

    for asset in assets:
        if not isinstance(asset, dict):
            continue

        code = (
            asset.get("code")
            or asset.get("symbol")
            or asset.get("name")
        )

        value = (
            asset.get("value")
            if "value" in asset
            else asset.get("price")
        )

        if code and value is not None:
            prices[code] = value

    return prices


def get_value(prices, code):
    if code not in prices:
        raise RuntimeError(
            f"Required asset not found: {code}"
        )

    return prices[code]


def create_report(prices):
    iran_time = get_iran_time()

    hour = iran_time.strftime("%H")
    minute = iran_time.strftime("%M")

    persian_digits = str.maketrans(
        "0123456789",
        "۰۱۲۳۴۵۶۷۸۹"
    )

    time_text = f"{hour}:{minute}".translate(
        persian_digits
    )

    date_text = get_jalali_date()

    usd = get_value(prices, ASSET_CODES["usd"])
    eur = get_value(prices, ASSET_CODES["eur"])

    gold_18 = get_value(
        prices,
        ASSET_CODES["gold_18"]
    )

    gold_24 = get_value(
        prices,
        ASSET_CODES["gold_24"]
    )

    gold_ounce = get_value(
        prices,
        ASSET_CODES["gold_ounce"]
    )

    sekkeh_emami = get_value(
        prices,
        ASSET_CODES["sekkeh_emami"]
    )

    nim_sekkeh = get_value(
        prices,
        ASSET_CODES["nim_sekkeh"]
    )

    rob_sekkeh = get_value(
        prices,
        ASSET_CODES["rob_sekkeh"]
    )

    bahar = get_value(
        prices,
        ASSET_CODES["bahar"]
    )

    gerami_sekkeh = get_value(
        prices,
        ASSET_CODES["gerami_sekkeh"]
    )

    silver_ounce = get_value(
        prices,
        ASSET_CODES["silver_ounce"]
    )

    bitcoin = get_value(
        prices,
        ASSET_CODES["bitcoin"]
    )

    report = f"""📊 بازارنما | Bazar Nama
📅 {date_text} | ⏰ {time_text}

💵 ارز
💵 دلار آزاد: {format_number(usd)} تومان
💶 یورو: {format_number(eur)} تومان

🥇 طلا
🟡 طلای ۱۸ عیار: {format_number(gold_18)} تومان
🟡 طلای ۲۴ عیار: {format_number(gold_24)} تومان
🌎 اونس طلا: {format_usd(gold_ounce)}

🪙 سکه
🔴 سکه امامی: {format_number(sekkeh_emami)} تومان
🟠 نیم‌سکه: {format_number(nim_sekkeh)} تومان
🟠 ربع‌سکه: {format_number(rob_sekkeh)} تومان
🟡 بهار آزادی: {format_number(bahar)} تومان
🟡 سکه گرمی: {format_number(gerami_sekkeh)} تومان

🥈 نقره
🥈 اونس نقره: {format_usd(silver_ounce)}

₿ ارز دیجیتال
₿ بیت‌کوین: {format_usd(bitcoin)}

🔗 @BazarNamaOfficial"""

    return report


def send_to_telegram(message):
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured."
        )

    if not TELEGRAM_CHAT_ID:
        raise RuntimeError(
            "TELEGRAM_CHAT_ID is not configured."
        )

    telegram_url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        telegram_url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        },
        timeout=30
    )

    if not response.ok:
        raise RuntimeError(
            "Telegram returned HTTP "
            f"{response.status_code}: "
            f"{response.text}"
        )

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(
            f"Telegram error: {result}"
        )

    return result


def validate_required_assets(prices):
    missing = []

    for name, code in ASSET_CODES.items():
        if code not in prices:
            missing.append(
                f"{name} ({code})"
            )

    if missing:
        raise RuntimeError(
            "Missing required assets: "
            + ", ".join(missing)
        )


def main():
    print("اتصال به Servix...")

    prices = get_prices()

    print(
        f"{len(prices)} دارایی دریافت شد."
    )

    validate_required_assets(prices)

    print("همه دارایی‌های موردنیاز موجود هستند.")

    report = create_report(prices)

    print("گزارش ساخته شد:")
    print(report)

    print("ارسال گزارش به تلگرام...")

    send_to_telegram(report)

    print("گزارش با موفقیت ارسال شد.")


if __name__ == "__main__":
    main()
