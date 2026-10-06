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

   
