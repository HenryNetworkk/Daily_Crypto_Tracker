
"""
processor.py — Tầng dữ liệu.
Nhận raw data từ fetcher, làm sạch, lưu vào prices.json,
và cung cấp các hàm query cho visualizer + updater dùng.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ── Đường dẫn tuyệt đối tính từ vị trí file này ──────────────────────────────
ROOT      = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "prices.json"


# ── Đọc / ghi ─────────────────────────────────────────────────────────────────
def _load() -> dict:
    """Đọc toàn bộ file JSON, trả về dict."""
    if not DATA_FILE.exists():
        logger.warning(f"⚠️  Không tìm thấy {DATA_FILE}, tạo mới.")
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        _save({"meta": {"created_at": _today(), "description": ""}, "records": []})

    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ── Xử lý record mới ──────────────────────────────────────────────────────────
def build_record(raw: dict) -> Optional[dict]:
    """
    Nhận dict thô từ fetcher.fetch_all(), trả về 1 record chuẩn.
    Trả None nếu thiếu dữ liệu quan trọng.
    """
    btc  = raw.get("bitcoin")
    gold = raw.get("gold")

    if not btc or not gold:
        logger.error("❌ Thiếu dữ liệu BTC hoặc vàng, bỏ qua.")
        return None

    return {
        "date"              : raw.get("date", _today()),
        # Bitcoin
        "btc_usd"           : btc["price_usd"],
        "btc_change_24h"    : btc["change_24h"],
        "btc_market_cap"    : btc["market_cap"],
        "btc_volume_24h"    : btc["volume_24h"],
        # Vàng
        "gold_usd_oz"       : gold["price_usd_oz"],
        "gold_usd_gram"     : gold["price_usd_gram"],
        "gold_vnd_gram"     : gold["price_vnd_gram"],
        # Meta
        "fetched_at"        : btc["fetched_at"],
    }


def save_record(record: dict) -> bool:
    """
    Append record vào prices.json.
    Nếu ngày hôm nay đã có thì ghi đè (tránh trùng khi chạy lại).
    Trả True nếu thành công.
    """
    data    = _load()
    records = data.setdefault("records", [])
    today   = record["date"]

    # Xoá record cũ cùng ngày nếu có
    before = len(records)
    records = [r for r in records if r.get("date") != today]
    if len(records) < before:
        logger.info(f"🔄 Ghi đè record ngày {today}")

    records.append(record)

    # Giữ tối đa 365 records gần nhất
    data["records"] = sorted(records, key=lambda r: r["date"])[-365:]

    _save(data)
    logger.info(f"💾 Đã lưu record {today} — tổng {len(data['records'])} ngày")
    return True


# ── Query helpers cho visualizer & updater ────────────────────────────────────
def get_latest() -> Optional[dict]:
    """Trả về record mới nhất."""
    records = _load().get("records", [])
    return records[-1] if records else None


def get_last_n_days(n: int = 30) -> list[dict]:
    """Trả về n record gần nhất, sắp xếp tăng dần theo ngày."""
    records = _load().get("records", [])
    return records[-n:]


def get_all() -> list[dict]:
    return _load().get("records", [])


def summary_stats(n: int = 30) -> dict:
    """
    Tính nhanh các chỉ số tóm tắt để hiển thị trong README.
    Dùng n ngày gần nhất.
    """
    records = get_last_n_days(n)
    if len(records) < 2:
        return {}

    btc_prices  = [r["btc_usd"]      for r in records]
    gold_prices = [r["gold_usd_oz"]  for r in records]

    def _pct_change(prices):
        return round((prices[-1] - prices[0]) / prices[0] * 100, 2)

    return {
        "period_days"     : len(records),
        "btc_high"        : max(btc_prices),
        "btc_low"         : min(btc_prices),
        "btc_change_pct"  : _pct_change(btc_prices),
        "gold_high"       : max(gold_prices),
        "gold_low"        : min(gold_prices),
        "gold_change_pct" : _pct_change(gold_prices),
    }

