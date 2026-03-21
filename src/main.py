import logging
import sys
from pathlib import Path

# Đảm bảo import được các module trong src/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetcher    import fetch_all
from processor  import build_record, save_record, get_latest, summary_stats

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(levelname)s] %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run():
    logger.info("=" * 50)
    logger.info("🚀 Bắt đầu cập nhật crypto dashboard")
    logger.info("=" * 50)

    # ── Bước 1: Fetch ──────────────────────────────────────────────────────────
    logger.info("📡 [1/4] Đang lấy dữ liệu từ API...")
    raw = fetch_all()

    # ── Bước 2: Process ────────────────────────────────────────────────────────
    logger.info("⚙️  [2/4] Đang xử lý và lưu dữ liệu...")
    record = build_record(raw)
    if not record:
        logger.error("💥 Không thể tạo record — dừng lại.")
        sys.exit(1)

    save_record(record)

    # ── Bước 3: Visualize ──────────────────────────────────────────────────────
    logger.info("📊 [3/4] Đang tạo chart...")
    try:
        from visualizer import generate_chart
        generate_chart()
    except Exception as e:
        # Chart lỗi thì vẫn tiếp tục — README vẫn update được
        logger.warning(f"⚠️  Chart lỗi (bỏ qua): {e}")

    # ── Bước 4: Update README ──────────────────────────────────────────────────
    logger.info("📝 [4/4] Đang cập nhật README...")
    try:
        from updater import update_readme
        latest = get_latest()
        stats  = summary_stats(30)
        update_readme(latest, stats)
    except Exception as e:
        logger.error(f"💥 Update README thất bại: {e}")
        sys.exit(1)

    logger.info("=" * 50)
    logger.info("✅ Hoàn tất! README đã được cập nhật.")
    logger.info("=" * 50)


if __name__ == "__main__":
    run()
