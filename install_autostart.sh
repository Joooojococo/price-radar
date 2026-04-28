#!/bin/bash
# 安裝開機自動啟動

echo "🚀 設定 BTC 雷達開機自動啟動"
echo "=================================="

# 創建日誌目錄
mkdir -p logs

# 複製 plist 到 LaunchAgents
PLIST_PATH=~/Library/LaunchAgents/com.btc.radar.plist

echo "📝 複製配置文件..."
cp com.btc.radar.plist "$PLIST_PATH"

# 載入服務
echo "🔧 載入服務..."
launchctl unload "$PLIST_PATH" 2>/dev/null
launchctl load "$PLIST_PATH"

echo ""
echo "✅ 安裝完成！"
echo ""
echo "📊 雷達已設定為開機自動啟動"
echo ""
echo "管理指令："
echo "  查看狀態: launchctl list | grep btc.radar"
echo "  停止服務: launchctl unload ~/Library/LaunchAgents/com.btc.radar.plist"
echo "  啟動服務: launchctl load ~/Library/LaunchAgents/com.btc.radar.plist"
echo "  查看日誌: tail -f logs/radar.log"
echo ""
echo "=================================="
