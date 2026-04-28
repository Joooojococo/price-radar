#!/bin/bash
# 測試 3 個 Telegram Bot

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

test_bot() {
    local name=$1
    local env_file=$2
    
    TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" "$SCRIPT_DIR/$env_file" | cut -d'=' -f2)
    CHAT_ID=$(grep "^TELEGRAM_CHAT_ID=" "$SCRIPT_DIR/$env_file" | cut -d'=' -f2)
    SYMBOL=$(grep "^SYMBOL=" "$SCRIPT_DIR/$env_file" | cut -d'=' -f2)
    
    if [ -z "$TOKEN" ] || [ -z "$CHAT_ID" ]; then
        echo "❌ $name: TOKEN 或 CHAT_ID 未填入"
        return
    fi
    
    MSG="✅ <b>$name 測試成功</b>%0A監控: $SYMBOL%0A時間: $(date '+%H:%M:%S')"
    
    RESULT=$(curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
        -d "chat_id=$CHAT_ID" \
        -d "text=$MSG" \
        -d "parse_mode=HTML")
    
    OK=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin).get('ok','false'))")
    
    if [ "$OK" = "True" ]; then
        echo "✅ $name ($SYMBOL): 發送成功！"
    else
        echo "❌ $name: 發送失敗 → $RESULT"
    fi
}

echo "======================================"
echo "  測試 3 個 Telegram Bot"
echo "======================================"

test_bot "BTC Bot" ".env.btc"
test_bot "ETH Bot" ".env.eth"
test_bot "洗盤 Bot" ".env.washout"

echo "======================================"
echo "  測試完成"
echo "======================================"
