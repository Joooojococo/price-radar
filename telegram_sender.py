#!/usr/bin/env python3
"""
Telegram 發送器
直接發送警報和截圖到 Telegram
"""

import os
from pathlib import Path
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

load_dotenv()


class TelegramSender:
    def __init__(self):
        """初始化 Telegram 發送器"""
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if self.bot_token and self.chat_id:
            self.bot = Bot(token=self.bot_token)
            print("✅ Telegram Bot 已配置")
        else:
            self.bot = None
            print("⚠️  Telegram Bot 未配置（可選）")

    def is_configured(self) -> bool:
        """檢查是否已配置"""
        return self.bot is not None

    async def send_message(self, message: str) -> bool:
        """發送純文字訊息"""
        if not self.is_configured():
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            print("✅ Telegram 訊息已發送")
            return True
            
        except TelegramError as e:
            print(f"❌ Telegram 發送失敗: {e}")
            return False

    async def send_photo(self, photo_path: str, caption: str = None) -> bool:
        """發送圖片"""
        if not self.is_configured():
            return False
        
        if not Path(photo_path).exists():
            print(f"❌ 圖片不存在: {photo_path}")
            return False
        
        try:
            with open(photo_path, 'rb') as photo:
                await self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode='HTML'
                )
            print("✅ Telegram 圖片已發送")
            return True
            
        except TelegramError as e:
            print(f"❌ Telegram 發送失敗: {e}")
            return False

    async def send_alert(self, message: str, screenshot_path: str = None) -> bool:
        """
        發送警報（訊息 + 截圖）
        """
        if not self.is_configured():
            return False
        
        try:
            # 如果有截圖，發送圖片並附帶訊息
            if screenshot_path and Path(screenshot_path).exists():
                with open(screenshot_path, 'rb') as photo:
                    await self.bot.send_photo(
                        chat_id=self.chat_id,
                        photo=photo,
                        caption=message,
                        parse_mode='HTML'
                    )
                print("✅ Telegram 警報已發送（含截圖）")
            else:
                # 只發送訊息
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='HTML'
                )
                print("✅ Telegram 警報已發送（純文字）")
            
            return True
            
        except TelegramError as e:
            print(f"❌ Telegram 發送失敗: {e}")
            return False

    async def upload_image(self, image_path: str) -> str:
        """
        上傳圖片並獲取 file_id
        可用於後續在 n8n 中引用
        """
        if not self.is_configured():
            return None
        
        try:
            with open(image_path, 'rb') as photo:
                message = await self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=photo
                )
            
            file_id = message.photo[-1].file_id
            print(f"✅ 圖片已上傳，file_id: {file_id}")
            return file_id
            
        except TelegramError as e:
            print(f"❌ 上傳圖片失敗: {e}")
            return None


# 測試函數
async def test_telegram():
    """測試 Telegram 發送"""
    sender = TelegramSender()
    
    if sender.is_configured():
        test_message = """
🚨 <b>測試警報</b>

這是一條測試訊息
時間: 2026-04-23 20:00:00

✅ 如果你收到這條訊息，表示 Telegram Bot 配置成功！
        """
        
        await sender.send_message(test_message)
    else:
        print("❌ Telegram Bot 未配置，請在 .env 中設定 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_telegram())
