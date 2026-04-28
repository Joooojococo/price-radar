#!/usr/bin/env python3
"""
系統測試工具 - 檢查所有功能是否正常
"""

import os
import asyncio
from dotenv import load_dotenv
import requests

load_dotenv()

print("=" * 60)
print("🧪 BTC 雷達系統測試")
print("=" * 60)

# 測試 1: 檢查環境變數
print("\n📋 測試 1: 檢查環境變數")
print("-" * 60)

deepseek_key = os.getenv('DEEPSEEK_API_KEY')
telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

if deepseek_key and deepseek_key != 'your_deepseek_api_key_here':
    print(f"✅ DeepSeek API Key: {deepseek_key[:20]}...")
else:
    print("❌ DeepSeek API Key 未設定")

if telegram_token and telegram_token != 'your_telegram_bot_token_here':
    print(f"✅ Telegram Bot Token: {telegram_token[:20]}...")
else:
    print("❌ Telegram Bot Token 未設定")

if telegram_chat_id and telegram_chat_id != 'your_telegram_chat_id_here':
    print(f"✅ Telegram Chat ID: {telegram_chat_id}")
else:
    print("❌ Telegram Chat ID 未設定")

# 測試 2: 測試 Binance 公開 API
print("\n🌐 測試 2: 測試 Binance 公開 API")
print("-" * 60)

try:
    url = "https://fapi.binance.com/fapi/v1/ticker/price"
    params = {'symbol': 'BTCUSDT'}
    response = requests.get(url, params=params, timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        price = float(data['price'])
        print(f"✅ Binance API 正常")
        print(f"   當前 BTC 價格: ${price:,.2f}")
    else:
        print(f"❌ Binance API 錯誤: {response.status_code}")
except Exception as e:
    print(f"❌ Binance API 連接失敗: {e}")

# 測試 3: 測試 Telegram Bot
print("\n📱 測試 3: 測試 Telegram Bot")
print("-" * 60)

if telegram_token and telegram_chat_id:
    try:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        data = {
            'chat_id': telegram_chat_id,
            'text': '🧪 <b>系統測試</b>\n\n✅ Telegram Bot 運作正常！\n\n這是一條測試訊息，確認推送功能正常。',
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            print("✅ Telegram Bot 正常")
            print("   測試訊息已發送到你的 Telegram")
        else:
            print(f"❌ Telegram Bot 錯誤: {response.status_code}")
            print(f"   回應: {response.text}")
    except Exception as e:
        print(f"❌ Telegram Bot 連接失敗: {e}")
else:
    print("⚠️  Telegram 未配置，跳過測試")

# 測試 4: 測試 DeepSeek API
print("\n🤖 測試 4: 測試 DeepSeek API")
print("-" * 60)

if deepseek_key and deepseek_key != 'your_deepseek_api_key_here':
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=deepseek_key,
            base_url="https://api.deepseek.com/v1"
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": "請回答：1+1=?"}
            ],
            max_tokens=50,
            timeout=10
        )
        
        answer = response.choices[0].message.content
        print("✅ DeepSeek API 正常")
        print(f"   測試回應: {answer}")
        
    except Exception as e:
        print(f"❌ DeepSeek API 錯誤: {e}")
else:
    print("⚠️  DeepSeek API 未配置，跳過測試")

# 測試 5: 模擬警報測試
print("\n🚨 測試 5: 模擬警報推送")
print("-" * 60)

if telegram_token and telegram_chat_id:
    try:
        # 模擬一個有力突破警報
        test_alert = """
🚨 <b>有力突破 警報</b> (測試)

<b>【交易對】</b>BTCUSDT
<b>【價格】</b>$77,800.00
<b>【時間】</b>21:35:00

<b>【技術指標】</b>
• CVD 斜率: 0.2500
• Vegas 上軌: $77,500.00
• OI: 98,500

<b>【AI 分析】</b>
• 信心評分: 9/10
• 分析: 這是一條測試警報
• 理由: 系統測試

<b>【操作建議】</b>
✅ 這是測試訊息
⚠️ 系統運作正常
📈 可以開始使用了
"""
        
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        data = {
            'chat_id': telegram_chat_id,
            'text': test_alert,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            print("✅ 模擬警報發送成功")
            print("   請檢查 Telegram 是否收到警報訊息")
        else:
            print(f"❌ 模擬警報發送失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 模擬警報失敗: {e}")
else:
    print("⚠️  Telegram 未配置，跳過測試")

# 總結
print("\n" + "=" * 60)
print("📊 測試總結")
print("=" * 60)
print("""
如果所有測試都通過（✅），系統就可以正常使用了！

系統會在偵測到以下情況時推送警報：
1. 🚨 有力突破 - 價格突破 Vegas 隧道 + CVD 強勢
2. ⚠️ 虛火假突破 - 價格創高但 CVD 背離

你可以：
• 讓系統繼續運行（等待真實警報）
• 調整參數（編輯 .env 文件）
• 查看即時監控數據
""")
print("=" * 60)
