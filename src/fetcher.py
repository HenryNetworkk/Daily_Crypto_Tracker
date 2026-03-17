"""
fetcher.py — Lấy giá Bitcoin, Vàng, tỷ giá USD/VNĐ.
"""

import requests
import logging
from datetime import datetime, timezone
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

COINGECKO_URL  = "https://api.coingecko.com/api/v3/simple/price"
METALS_URL     = "https://api.metals.live/v1/spot"
GOLD_FALLBACK  = "https://api.frankfurter.app/latest?from=XAU&to=USD"
EXCHANGE_URL   = "https://api.exchangerate-api.com/v4/latest/USD"
TIMEOUT        = 15


def fetch_usd_vnd() -> float:
    try:
        resp = requests.get(EXCHANGE_URL, timeout=TIMEOUT)
        resp.raise_for_status()
        rate = float(resp.json()["rates"]["VND"])
        logger.info(f"💱 Tỷ giá: 1 USD = {rate:,.0f} VNĐ")
        return rate
    except Exception as e:
        logger.warning(f"⚠️ Không lấy được tỷ giá ({e}), dùng mặc định 25,000")
        return 25_000.0


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


def _parse_gold(price_oz: float, usd_vnd: float) -> dict:
    price_gram = round(price_oz / 31.1035, 2)
    return {
        "price_usd_oz"  : round(price_oz, 2),
        "price_usd_gram": price_gram,
        "price_vnd_gram": int(price_gram * usd_vnd),
        "fetched_at"    : datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def fetch_gold(usd_vnd: float) -> Optional[dict]:
    # Thử nguồn chính
    try:
        resp = requests.get(METALS_URL, timeout=TIMEOUT)
        resp.raise_for_status()
        for item in resp.json():
            if "gold" in item:
                price_oz = float(item["gold"])
                result = _parse_gold(price_oz, usd_vnd)
                logger.info(f"✅ Vàng: ${price_oz:,.2f}/oz | {result['price_vnd_gram']:,} VNĐ/g")
                return result
        raise ValueError("Không tìm thấy key gold")
    except Exception as e:
        logger.warning(f"⚠️ metals.live lỗi ({e}), thử fallback...")

    # Fallback ECB
    try:
        resp = requests.get(GOLD_FALLBACK, timeout=TIMEOUT)
        resp.raise_for_status()
        price_oz = float(resp.json()["rates"]["USD"])
        result = _parse_gold(price_oz, usd_vnd)
        logger.info(f"✅ Vàng (fallback): ${price_oz:,.2f}/oz")
        return result
    except Exception as e:
        logger.error(f"❌ Cả 2 nguồn vàng đều lỗi: {e}")
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
