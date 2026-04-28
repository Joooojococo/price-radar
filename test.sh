#!/bin/bash
# 測試 BTC 監控系統各個組件

echo "🧪 測試 BTC 監控系統..."
echo "=================================="

# 啟動虛擬環境
source venv/bin/activate

# 測試 1: 檢查環境變數
echo ""
echo "📋 測試 1: 檢查環境變數..."
if [ -f .env ]; then
    echo "✅ .env 文件存在"
    
    # 檢查必要的環境變數
    source .env
    
    if [ -z "$BINANCE_API_KEY" ] || [ "$BINANCE_API_KEY" = "your_binance_api_key_here" ]; then
        echo "⚠️  BINANCE_API_KEY 未設定"
    else
        echo "✅ BINANCE_API_KEY 已設定"
    fi
    
    if [ -z "$N8N_WEBHOOK_URL" ] || [ "$N8N_WEBHOOK_URL" = "https://your-n8n-instance.com/webhook/btc-alert" ]; then
        echo "⚠️  N8N_WEBHOOK_URL 未設定"
    else
        echo "✅ N8N_WEBHOOK_URL 已設定"
    fi
    
    if [ -z "$TRADINGVIEW_CHART_URL" ]; then
        echo "⚠️  TRADINGVIEW_CHART_URL 未設定"
    else
        echo "✅ TRADINGVIEW_CHART_URL 已設定"
    fi
else
    echo "❌ .env 文件不存在"
    exit 1
fi

# 測試 2: 測試 Telegram Bot
echo ""
echo "📱 測試 2: 測試 Telegram Bot..."
python3 telegram_sender.py

# 測試 3: 測試截圖功能
echo ""
echo "📸 測試 3: 測試截圖功能..."
echo "⚠️  這將開啟瀏覽器並截圖，可能需要幾秒鐘..."
python3 screenshot_handler.py

# 測試 4: 檢查 Python 依賴
echo ""
echo "📦 測試 4: 檢查 Python 依賴..."
python3 -c "
import sys
try:
    import binance
    print('✅ python-binance')
except ImportError:
    print('❌ python-binance 未安裝')
    sys.exit(1)

try:
    import pandas
    print('✅ pandas')
except ImportError:
    print('❌ pandas 未安裝')
    sys.exit(1)

try:
    import numpy
    print('✅ numpy')
except ImportError:
    print('❌ numpy 未安裝')
    sys.exit(1)

try:
    import playwright
    print('✅ playwright')
except ImportError:
    print('❌ playwright 未安裝')
    sys.exit(1)

try:
    import telegram
    print('✅ python-telegram-bot')
except ImportError:
    print('❌ python-telegram-bot 未安裝')
    sys.exit(1)

print('✅ 所有依賴已安裝')
"

echo ""
echo "=================================="
echo "✅ 測試完成！"
echo ""
echo "如果所有測試都通過，可以執行："
echo "  ./start.sh"
echo ""
echo "開始監控 BTC"
echo "=================================="
