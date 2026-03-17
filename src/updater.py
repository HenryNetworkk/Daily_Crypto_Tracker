import logging
import re
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

ROOT        = Path(__file__).resolve().parent.parent
README_PATH = ROOT / "README.md"

# Cặp tag đánh dấu vùng tự động cập nhật
START_TAG = "<!-- PRICE_START -->"
END_TAG   = "<!-- PRICE_END -->"


# ── Helpers định dạng ──────────────────────────────────────────────────────────
def _arrow(change: float) -> str:
    """Trả về emoji mũi tên + màu tùy theo chiều thay đổi."""
    return "🟢 ▲" if change >= 0 else "🔴 ▼"


def _fmt_large(n: float) -> str:
    """Rút gọn số lớn: 1_320_000_000_000 → $1.32T"""
    if n >= 1e12: return f"${n/1e12:.2f}T"
    if n >= 1e9:  return f"${n/1e9:.2f}B"
    if n >= 1e6:  return f"${n/1e6:.2f}M"
    return f"${n:,.0f}"


def _build_block(latest: dict, stats: dict) -> str:
    """
    Tạo markdown block sẽ chèn vào giữa 2 tag.
    Trả về chuỗi hoàn chỉnh (bao gồm cả dòng trống đầu/cuối).
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    btc_arrow  = _arrow(latest["btc_change_24h"])
    btc_sign   = "+" if latest["btc_change_24h"] >= 0 else ""
    gold_arrow = "📈" if stats.get("gold_change_pct", 0) >= 0 else "📉"
    gold_sign  = "+" if stats.get("gold_change_pct", 0) >= 0 else ""
    period     = stats.get("period_days", "?")

    block = f"""
## 📊 Giá hôm nay — {latest['date']}

> ⏱️ Tự động cập nhật lúc **{now}** bởi [GitHub Actions](.github/workflows/update.yml)

### ₿ Bitcoin

| | Giá trị |
|---|---|
| 💰 Giá hiện tại | **${latest['btc_usd']:,.2f}** |
| {btc_arrow} Thay đổi 24h | `{btc_sign}{latest['btc_change_24h']:.2f}%` |
| 📦 Market Cap | {_fmt_large(latest['btc_market_cap'])} |
| 🔄 Volume 24h | {_fmt_large(latest['btc_volume_24h'])} |

### 🥇 Vàng (XAU)

| | Giá trị |
|---|---|
| 💰 Giá / troy oz | **${latest['gold_usd_oz']:,.2f}** |
| ⚖️ Giá / gram | ${latest['gold_usd_gram']:,.2f} |
| 🇻🇳 Giá / gram (VNĐ) | {latest['gold_vnd_gram']:,} ₫ |

### 📈 Thống kê {period} ngày qua

| | Bitcoin | Vàng |
|---|---|---|
| 🔺 Cao nhất | ${stats.get('btc_high', 0):,.0f} | ${stats.get('gold_high', 0):,.0f}/oz |
| 🔻 Thấp nhất | ${stats.get('btc_low', 0):,.0f} | ${stats.get('gold_low', 0):,.0f}/oz |
| {gold_arrow} Thay đổi | `{btc_sign}{stats.get('btc_change_pct', 0):.1f}%` | `{gold_sign}{stats.get('gold_change_pct', 0):.1f}%` |

### 📉 Biểu đồ 30 ngày

![Price Chart](assets/chart.png)

"""
    return block


def update_readme(latest: dict, stats: dict) -> bool:
    """
    Đọc README.md, thay vùng giữa 2 tag, ghi lại.
    Nếu tag chưa có trong README thì append vào cuối.
    """
    if not latest:
        logger.error("❌ Không có data để update README.")
        return False

    # Tạo README mặc định nếu chưa có
    if not README_PATH.exists():
        logger.info("📄 Tạo README.md mới...")
        README_PATH.write_text(_default_readme(), encoding="utf-8")

    content = README_PATH.read_text(encoding="utf-8")
    new_block = _build_block(latest, stats)

    if START_TAG in content and END_TAG in content:
        # Thay thế phần giữa 2 tag
        pattern = re.compile(
            re.escape(START_TAG) + r".*?" + re.escape(END_TAG),
            re.DOTALL,
        )
        new_content = pattern.sub(
            START_TAG + new_block + END_TAG,
            content,
        )
        logger.info("🔄 Đã cập nhật vùng giá trong README.")
    else:
        # Tag chưa có → append vào cuối
        new_content = content.rstrip() + f"\n\n{START_TAG}{new_block}{END_TAG}\n"
        logger.info("➕ Đã thêm vùng giá vào cuối README.")

    README_PATH.write_text(new_content, encoding="utf-8")
    logger.info(f"✅ README.md đã ghi xong ({len(new_content)} ký tự)")
    return True


def _default_readme() -> str:
    """README mặc định khi file chưa tồn tại."""
    return f"""# 📊 Crypto & Gold Dashboard

Dự án tự động cập nhật giá Bitcoin và Vàng hàng ngày qua GitHub Actions.

{START_TAG}
{END_TAG}

## 🛠️ Cách hoạt động

1. **GitHub Actions** chạy lúc 8:00 SA (GMT+7) mỗi ngày
2. Python fetch giá từ [CoinGecko](https://coingecko.com) và [metals.live](https://metals.live)
3. Lưu lịch sử vào `data/prices.json`
4. Tạo chart từ 30 ngày gần nhất
5. Tự commit và push lên repo này

## 📁 Cấu trúc

```
crypto-dashboard/
├── src/
│   ├── fetcher.py      # Lấy dữ liệu từ API
│   ├── processor.py    # Lưu lịch sử
│   ├── visualizer.py   # Tạo chart
│   ├── updater.py      # Cập nhật README
│   └── main.py
├── data/prices.json    # Lịch sử giá
└── assets/chart.png    # Biểu đồ
```
"""


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    logging.basicConfig(level=logging.INFO)
    from processor import get_latest, summary_stats
    update_readme(get_latest(), summary_stats(30))
