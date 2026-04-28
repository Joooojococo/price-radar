#!/usr/bin/env python3
"""
獲取 Telegram Chat ID 的小工具
"""

import requests

# 你的 Bot Token
BOT_TOKEN = "8662228818:AAGHQpYoDgAmXQOJbb0mmmLG34gCt7m5oQM"

print("🤖 Telegram Chat ID 獲取工具")
print("=" * 60)
print("\n📝 步驟：")
print("1. 在 Telegram 搜尋你的 Bot")
print("2. 發送 /start 給 Bot")
print("3. 然後按 Enter 繼續...")
input()

print("\n🔍 正在獲取 Chat ID...")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    
    if data['result']:
        for update in data['result']:
            if 'message' in update:
                chat_id = update['message']['chat']['id']
                username = update['message']['chat'].get('username', 'N/A')
                first_name = update['message']['chat'].get('first_name', 'N/A')
                
                print(f"\n✅ 找到 Chat ID！")
                print(f"   Chat ID: {chat_id}")
                print(f"   用戶名: {username}")
                print(f"   名字: {first_name}")
                print(f"\n📋 請複製這個 Chat ID: {chat_id}")
                break
    else:
        print("\n❌ 沒有找到訊息")
        print("請確保你已經：")
        print("1. 在 Telegram 搜尋你的 Bot")
        print("2. 發送 /start 給 Bot")
else:
    print(f"\n❌ API 請求失敗: {response.status_code}")
    print("請檢查 Bot Token 是否正確")
