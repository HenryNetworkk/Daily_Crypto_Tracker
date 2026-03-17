
#!/usr/bin/env bash
# Dùng để test trên máy local, không cần GitHub Actions
set -e  # dừng ngay nếu có lỗi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."

echo "📦 Cài thư viện..."
pip install -r "$ROOT/requirements.txt" -q

echo "🚀 Chạy pipeline..."
cd "$ROOT"
python src/main.py

echo "✅ Xong! Kiểm tra README.md và data/prices.json"
