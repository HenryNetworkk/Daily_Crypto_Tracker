
"""
fetcher.py — Lấy giá Bitcoin và Vàng từ các API miễn phí.
- Bitcoin : CoinGecko API (free, no key needed)
- Vàng    : GoldAPI.io hoặc fallback sang metals-api
"""

import requests
import logging
from datetime import datetime, timezone
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Cấu hình ──────────────────────────────────────────────────────────────────
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
METALS_API_URL = "https://api.metals.live/v1/spot"   # Free, no key
TIMEOUT = 15  # seconds


# ── Bitcoin ───────────────────────────────────────────────────────────────────
def fetch_bitcoin() -> Optional[dict]:
    """
    Trả về dict:
    {
        "price_usd": 67423.12,
        "change_24h": 2.35,      # % thay đổi 24h
        "market_cap": 1.32e12,
        "volume_24h": 28.4e9,
        "fetched_at": "2025-01-15T08:00:00Z"
    }
    """
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
            "price_usd": round(data["usd"], 2),
            "change_24h": round(data["usd_24h_change"], 2),
            "market_cap": data["usd_market_cap"],
            "volume_24h": data["usd_24h_vol"],
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        logger.info(f"✅ Bitcoin: ${result['price_usd']:,.2f} ({result['change_24h']:+.2f}%)")
        return result

    except requests.RequestException as e:
        logger.error(f"❌ Lỗi fetch Bitcoin: {e}")
        return None


# ── Vàng ──────────────────────────────────────────────────────────────────────
def fetch_gold() -> Optional[dict]:
    """
    Trả về dict:
    {
        "price_usd_oz": 2345.67,   # Giá mỗi troy ounce (USD)
        "price_usd_gram": 75.42,
        "price_vnd_gram": 1890000, # Quy đổi sang VNĐ (ước tính)
        "fetched_at": "..."
    }
    """
    try:
        resp = requests.get(METALS_API_URL, timeout=TIMEOUT)
        resp.raise_for_status()
        metals = resp.json()

        # metals.live trả về list [{"gold": price}, {"silver": price}, ...]
        gold_price_oz = None
        for item in metals:
            if "gold" in item:
                gold_price_oz = float(item["gold"])
                break

        if gold_price_oz is None:
            raise ValueError("Không tìm thấy giá vàng trong response")

        price_gram = round(gold_price_oz / 31.1035, 2)   # 1 troy oz = 31.1035 g
        # Tỷ giá USD/VNĐ ước tính — có thể fetch thêm nếu cần
        usd_vnd_rate = 25_000
        price_vnd_gram = int(price_gram * usd_vnd_rate)

        result = {
            "price_usd_oz": round(gold_price_oz, 2),
            "price_usd_gram": price_gram,
            "price_vnd_gram": price_vnd_gram,
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        logger.info(f"✅ Vàng: ${gold_price_oz:,.2f}/oz | {price_vnd_gram:,} VNĐ/g")
        return result

    except (requests.RequestException, ValueError, KeyError) as e:
        logger.error(f"❌ Lỗi fetch Gold: {e}")
        return None


# ── Entry point ───────────────────────────────────────────────────────────────
def fetch_all() -> dict:
    """Gọi cả 2, trả về dict tổng hợp."""
    logger.info("🔄 Bắt đầu fetch giá...")
    return {
        "bitcoin": fetch_bitcoin(),
        "gold": fetch_gold(),
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


if __name__ == "__main__":
    import json
    data = fetch_all()
    print(json.dumps(data, indent=2, ensure_ascii=False))
