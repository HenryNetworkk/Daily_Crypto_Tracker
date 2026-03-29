"""
fetcher.py — Lấy giá Bitcoin, Vàng, tỷ giá USD/VNĐ.
Tất cả dùng CoinGecko — free, không cần API key.
"""

import requests
import logging
from datetime import datetime, timezone
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
EXCHANGE_URL  = "https://api.exchangerate-api.com/v4/latest/USD"
TIMEOUT       = 15


def fetch_usd_vnd() -> float:
    try:
        resp = requests.get(EXCHANGE_URL, timeout=TIMEOUT)
        resp.raise_for_status()
        rate = float(resp.json()["rates"]["VND"])
        logger.info(f"💱 Tỷ giá: 1 USD = {rate:,.0f} VNĐ")
        return rate
    except Exception as e:
        logger.warning(f"⚠️ Không lấy được tỷ giá ({e}), dùng mặc định 26,000")
        return 26_000.0


def fetch_bitcoin() -> Optional[dict]:
    try:
        params = {
            "ids": "bitcoin",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
        }
        resp = requests.get(COINGECKO_URL, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()["bitcoin"]
        result = {
            "price_usd"  : round(data["usd"], 2),
            "change_24h" : round(data["usd_24h_change"], 2),
            "market_cap" : data["usd_market_cap"],
            "volume_24h" : data["usd_24h_vol"],
            "fetched_at" : datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        logger.info(f"✅ Bitcoin: ${result['price_usd']:,.2f} ({result['change_24h']:+.2f}%)")
        return result
    except Exception as e:
        logger.error(f"❌ Lỗi fetch Bitcoin: {e}")
        return None


def fetch_gold(usd_vnd: float) -> Optional[dict]:
    """
    Dùng PAXG (Pax Gold) từ CoinGecko — token vàng thật, giá bám 1:1 với XAU/USD.
    Cùng nguồn với Bitcoin nên không bao giờ lỗi riêng.
    """
    try:
        params = {
            "ids": "pax-gold",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        }
        resp = requests.get(COINGECKO_URL, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()["pax-gold"]

        price_oz   = round(data["usd"], 2)          # giá 1 troy oz
        price_gram = round(price_oz / 31.1035, 2)   # 1 troy oz = 31.1035g

        result = {
            "price_usd_oz"  : price_oz,
            "price_usd_gram": price_gram,
            "price_vnd_gram": int(price_gram * usd_vnd),
            "fetched_at"    : datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        logger.info(f"✅ Vàng (PAXG): ${price_oz:,.2f}/oz | {result['price_vnd_gram']:,} VNĐ/g")
        return result
    except Exception as e:
        logger.error(f"❌ Lỗi fetch Gold: {e}")
        return None


def fetch_all() -> dict:
    logger.info("🔄 Bắt đầu fetch dữ liệu...")
    usd_vnd = fetch_usd_vnd()
    return {
        "bitcoin" : fetch_bitcoin(),
        "gold"    : fetch_gold(usd_vnd),
        "usd_vnd" : usd_vnd,
        "date"    : datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


if __name__ == "__main__":
    import json
    data = fetch_all()
    print(json.dumps(data, indent=2, ensure_ascii=False))
