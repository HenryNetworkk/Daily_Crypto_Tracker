"""
notifier.py — Gửi Telegram khi BTC hoặc vàng thay đổi > ngưỡng.
Setup: tạo bot qua @BotFather, lấy token + chat_id
Thêm vào GitHub Secrets: TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
"""

import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

TELEGRAM_URL = "https://api.telegram.org/bot{token}/sendMessage"

# Ngưỡng cảnh báo
BTC_ALERT_PCT  = 5.0   # Cảnh báo khi BTC thay đổi > 5% trong 24h
GOLD_ALERT_PCT = 2.0   # Cảnh báo khi vàng thay đổi > 2% trong 24h


def _send(token: str, chat_id: str, text: str) -> bool:
    try:
        resp = requests.post(
            TELEGRAM_URL.format(token=token),
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("📨 Telegram: đã gửi cảnh báo.")
        return True
    except Exception as e:
        logger.warning(f"⚠️  Telegram lỗi: {e}")
        return False


def check_and_notify(latest: dict, stats: dict) -> None:
    token   = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.info("ℹ️  Bỏ qua Telegram (chưa cấu hình secrets).")
        return

    alerts = []
    btc_chg  = latest.get("btc_change_24h", 0)
    gold_chg = stats.get("gold_change_pct", 0)

    if abs(btc_chg) >= BTC_ALERT_PCT:
        icon = "🚀" if btc_chg > 0 else "💥"
        alerts.append(
            f"{icon} <b>Bitcoin</b> {btc_chg:+.2f}% trong 24h\n"
            f"   Giá hiện tại: <b>${latest['btc_usd']:,.0f}</b>"
        )

    if abs(gold_chg) >= GOLD_ALERT_PCT:
        icon = "📈" if gold_chg > 0 else "📉"
        alerts.append(
            f"{icon} <b>Vàng</b> {gold_chg:+.1f}% trong {stats.get('period_days','?')} ngày\n"
            f"   Giá hiện tại: <b>${latest['gold_usd_oz']:,.0f}/oz</b>"
        )

    if alerts:
        msg = "🔔 <b>Crypto Dashboard Alert</b>\n\n" + "\n\n".join(alerts)
        _send(token, chat_id, msg)
