#!/bin/bash
# 移除開機自動啟動

echo "🛑 移除 BTC 雷達開機自動啟動"
echo "=================================="

PLIST_PATH=~/Library/LaunchAgents/com.btc.radar.plist

# 卸載服務
echo "🔧 卸載服務..."
launchctl unload "$PLIST_PATH" 2>/dev/null

# 刪除 plist
echo "🗑️  刪除配置文件..."
rm -f "$PLIST_PATH"

echo ""
echo "✅ 移除完成！"
echo ""
echo "雷達已不會開機自動啟動"
echo "你仍可以手動執行: python3 simple_scanner.py"
echo ""
echo "=================================="
