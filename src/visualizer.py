"""
visualizer.py — Tạo chart.png từ lịch sử 30 ngày.
Dùng matplotlib với style tối, 2 panel: BTC (trên) + Vàng (dưới).
"""

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Không cần GUI — bắt buộc khi chạy trên server
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyArrowPatch
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

ROOT       = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets"
CHART_PATH = ASSETS_DIR / "chart.png"

# ── Màu sắc ────────────────────────────────────────────────────────────────────
BG_DARK    = "#0d1117"   # Nền ngoài (giống GitHub dark)
BG_PANEL   = "#161b22"   # Nền panel
BTC_COLOR  = "#f7931a"   # Cam Bitcoin
GOLD_COLOR = "#ffd700"   # Vàng
TEXT_MAIN  = "#e6edf3"
TEXT_DIM   = "#8b949e"
GRID_COLOR = "#21262d"
UP_COLOR   = "#3fb950"   # Xanh lá — tăng
DOWN_COLOR = "#f85149"   # Đỏ — giảm


def _parse_dates(records: list[dict]) -> list[datetime]:
    return [datetime.strptime(r["date"], "%Y-%m-%d") for r in records]


def _add_area(ax, dates, values, color: str):
    """Vẽ đường + vùng gradient phía dưới."""
    ax.plot(dates, values, color=color, linewidth=1.8, zorder=3)
    ax.fill_between(dates, values, min(values), alpha=0.15, color=color, zorder=2)


def _add_change_badge(ax, values: list, color: str, fmt: str = "${:,.0f}"):
    """Hiển thị % thay đổi ở góc trên phải panel."""
    if len(values) < 2:
        return
    pct = (values[-1] - values[0]) / values[0] * 100
    sign = "+" if pct >= 0 else ""
    badge_color = UP_COLOR if pct >= 0 else DOWN_COLOR
    ax.text(
        0.98, 0.92,
        f"{sign}{pct:.1f}% (30 ngày)",
        transform=ax.transAxes,
        ha="right", va="top",
        fontsize=9, color=badge_color,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=BG_PANEL,
                  edgecolor=badge_color, linewidth=0.8, alpha=0.9),
    )


def _style_axis(ax, ylabel: str):
    """Áp chung style cho 1 panel."""
    ax.set_facecolor(BG_PANEL)
    ax.tick_params(colors=TEXT_DIM, labelsize=8)
    ax.set_ylabel(ylabel, color=TEXT_DIM, fontsize=9, labelpad=8)
    ax.yaxis.set_label_position("right")
    ax.yaxis.tick_right()
    ax.grid(True, color=GRID_COLOR, linewidth=0.6, linestyle="-", zorder=1)
    ax.spines[:].set_color(GRID_COLOR)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0)
    # Format số trục Y gọn hơn
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
    )


def generate_chart(n_days: int = 30) -> Path:
    """
    Tạo chart.png, lưu vào assets/chart.png.
    Trả về Path của file đã lưu.
    """
    from processor import get_last_n_days
    records = get_last_n_days(n_days)

if len(records) < 1:
        logger.warning("⚠️  Chưa đủ dữ liệu để vẽ chart (cần ≥ 1 ngày).")
        return None

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    dates      = _parse_dates(records)
    btc_vals   = [r["btc_usd"]      for r in records]
    gold_vals  = [r["gold_usd_oz"]  for r in records]
    latest_btc  = records[-1]["btc_usd"]
    latest_gold = records[-1]["gold_usd_oz"]
    latest_date = records[-1]["date"]

    # ── Layout ────────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(10, 6), facecolor=BG_DARK)
    fig.subplots_adjust(left=0.04, right=0.88, top=0.88, bottom=0.1, hspace=0.35)

    ax1 = fig.add_subplot(2, 1, 1)   # BTC
    ax2 = fig.add_subplot(2, 1, 2)   # Gold

    # ── Tiêu đề tổng ─────────────────────────────────────────────────────────
    fig.text(
        0.04, 0.95,
        "₿  Bitcoin  &  🥇  Gold  —  30-day tracker",
        color=TEXT_MAIN, fontsize=13, fontweight="bold", va="top",
    )
    fig.text(
        0.04, 0.91,
        f"Cập nhật: {latest_date}  |  BTC ${latest_btc:,.0f}  |  Gold ${latest_gold:,.0f}/oz",
        color=TEXT_DIM, fontsize=8.5, va="top",
    )

    # ── Panel 1: BTC ─────────────────────────────────────────────────────────
    _add_area(ax1, dates, btc_vals, BTC_COLOR)
    _style_axis(ax1, "USD")
    ax1.set_title("Bitcoin (BTC/USD)", color=TEXT_MAIN, fontsize=10,
                  fontweight="bold", loc="left", pad=6)
    _add_change_badge(ax1, btc_vals, BTC_COLOR)

    # Chấm điểm hiện tại
    ax1.scatter([dates[-1]], [btc_vals[-1]], color=BTC_COLOR, s=40, zorder=5)

    # ── Panel 2: Gold ─────────────────────────────────────────────────────────
    _add_area(ax2, dates, gold_vals, GOLD_COLOR)
    _style_axis(ax2, "USD/oz")
    ax2.set_title("Vàng (XAU/USD)", color=TEXT_MAIN, fontsize=10,
                  fontweight="bold", loc="left", pad=6)
    _add_change_badge(ax2, gold_vals, GOLD_COLOR)
    ax2.scatter([dates[-1]], [gold_vals[-1]], color=GOLD_COLOR, s=40, zorder=5)

    # ── Watermark ─────────────────────────────────────────────────────────────
    fig.text(
        0.88, 0.02, "auto-updated by GitHub Actions",
        color=TEXT_DIM, fontsize=7, ha="right", alpha=0.5,
    )

    plt.savefig(CHART_PATH, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
    plt.close(fig)

    logger.info(f"📊 Chart đã lưu → {CHART_PATH}")
    return CHART_PATH


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    path = generate_chart()
    print(f"Saved: {path}")
