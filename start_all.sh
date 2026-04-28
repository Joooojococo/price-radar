#!/bin/bash
# ICT + Gann + Candlestick Strategy — 一鍵啟動 3 Bot

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================"
echo "  ICT + Gann Scanner — 2 Bot 系統"
echo "======================================"

# Bot 1: BTC 標準信號
echo "🟡 啟動 BTC Bot (BTCUSDT)..."
env $(grep -v '^#' .env.btc | xargs) python3 ict_gann_scanner.py &
BTC_PID=$!
echo "✅ BTC Bot PID: $BTC_PID"
sleep 2

# Bot 2: BTC 超強信號 (BB突破 only)
echo "🔴 啟動 超強信號 Bot (BB突破)..."
env $(grep -v '^#' .env.washout | xargs) python3 ict_gann_scanner.py &
WASHOUT_PID=$!
echo "✅ 超強信號 Bot PID: $WASHOUT_PID"

echo ""
echo "======================================"
echo "  2 Bot 已啟動！按 Ctrl+C 停止全部"
echo "======================================"

trap "kill $BTC_PID $WASHOUT_PID 2>/dev/null; echo '⏹️  所有 Bot 已停止'" INT TERM
wait $BTC_PID $WASHOUT_PID
