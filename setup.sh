#!/bin/bash
# BTC 監控系統 - 自動安裝腳本

echo "🚀 開始安裝 BTC 高頻監控系統..."
echo "=================================="

# 檢查 Python 版本
echo "📌 檢查 Python 版本..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ 未找到 Python 3，請先安裝 Python 3.8+"
    exit 1
fi

# 創建虛擬環境
echo ""
echo "📦 創建虛擬環境..."
python3 -m venv venv

# 啟動虛擬環境
echo "🔧 啟動虛擬環境..."
source venv/bin/activate

# 升級 pip
echo "⬆️  升級 pip..."
pip install --upgrade pip

# 安裝依賴
echo ""
echo "📥 安裝 Python 依賴..."
pip install -r requirements.txt

# 安裝 Playwright 瀏覽器
echo ""
echo "🌐 安裝 Playwright 瀏覽器..."
playwright install chromium

# 創建必要的目錄
echo ""
echo "📁 創建目錄..."
mkdir -p screenshots
mkdir -p logs

# 複製環境變數範例
if [ ! -f .env ]; then
    echo ""
    echo "📝 創建 .env 文件..."
    cp .env.example .env
    echo "✅ 已創建 .env 文件，請編輯並填入你的 API 金鑰"
else
    echo "⚠️  .env 文件已存在，跳過"
fi

# 設定執行權限
echo ""
echo "🔐 設定執行權限..."
chmod +x scanner.py
chmod +x start.sh
chmod +x test.sh

echo ""
echo "=================================="
echo "✅ 安裝完成！"
echo ""
echo "📝 下一步："
echo "1. 編輯 .env 文件，填入你的配置："
echo "   - BINANCE_API_KEY"
echo "   - BINANCE_API_SECRET"
echo "   - N8N_WEBHOOK_URL"
echo "   - TELEGRAM_BOT_TOKEN (可選)"
echo "   - TELEGRAM_CHAT_ID (可選)"
echo "   - TRADINGVIEW_CHART_URL"
echo ""
echo "2. 測試系統："
echo "   ./test.sh"
echo ""
echo "3. 啟動監控："
echo "   ./start.sh"
echo ""
echo "=================================="
