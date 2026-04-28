#!/usr/bin/env python3
"""
Token 用量監控
當 DeepSeek Token 不足時發送警告
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import asyncio

load_dotenv()

class TokenMonitor:
    def __init__(self):
        """初始化 Token 監控器"""
        self.deepseek_enabled = True
        self.token_error_count = 0
        self.max_errors = 3
        self.last_warning_time = None
        self.warning_cooldown = 3600  # 1 小時警告一次
        
    def record_token_error(self):
        """記錄 Token 錯誤"""
        self.token_error_count += 1
        
        if self.token_error_count >= self.max_errors:
            print(f"\n⚠️  DeepSeek Token 可能已用完（連續 {self.max_errors} 次錯誤）")
            print("🔄 切換到無 AI 模式（只使用技術指標）")
            self.deepseek_enabled = False
            return True
        
        return False
    
    def reset_error_count(self):
        """重置錯誤計數"""
        self.token_error_count = 0
    
    def should_send_warning(self) -> bool:
        """檢查是否應該發送警告"""
        if self.last_warning_time is None:
            return True
        
        time_since_last = (datetime.now() - self.last_warning_time).total_seconds()
        return time_since_last >= self.warning_cooldown
    
    async def send_token_warning(self, telegram_sender):
        """發送 Token 警告到 Telegram"""
        if not self.should_send_warning():
            return
        
        warning_message = """
⚠️ <b>DeepSeek Token 警告</b>

🔴 DeepSeek API Token 可能已用完

<b>【當前狀態】</b>
• 系統已切換到無 AI 模式
• 只使用技術指標（Vegas + CVD）
• 警報仍會正常推送

<b>【解決方案】</b>
1. 檢查 DeepSeek 帳號配額
2. 充值或等待配額重置
3. 或繼續使用無 AI 模式

<b>【影響】</b>
• ❌ 無 AI 信心評分
• ✅ Vegas 隧道正常
• ✅ CVD 分析正常
• ✅ 警報推送正常

系統會繼續監控，但建議盡快處理。
"""
        
        try:
            await telegram_sender.send_alert(warning_message, None)
            self.last_warning_time = datetime.now()
            print("✅ Token 警告已發送到 Telegram")
        except Exception as e:
            print(f"❌ 發送 Token 警告失敗: {e}")
