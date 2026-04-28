#!/usr/bin/env python3
"""
語音警報系統
在電腦喇叭播放語音提示
"""

import os
import platform
import pyttsx3
from dotenv import load_dotenv

load_dotenv()


class VoiceAlert:
    def __init__(self):
        """初始化語音警報系統"""
        self.enabled = os.getenv('VOICE_ALERT_ENABLED', 'true').lower() == 'true'
        self.language = os.getenv('VOICE_LANGUAGE', 'zh-TW')
        
        if self.enabled:
            try:
                self.engine = pyttsx3.init()
                
                # 設定語音參數
                self.engine.setProperty('rate', 150)  # 語速
                self.engine.setProperty('volume', 1.0)  # 音量
                
                # 嘗試設定中文語音
                voices = self.engine.getProperty('voices')
                for voice in voices:
                    if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                
                print("✅ 語音警報系統已啟用")
                
            except Exception as e:
                print(f"⚠️  語音引擎初始化失敗: {e}")
                self.enabled = False
        else:
            self.engine = None
            print("⚠️  語音警報已停用")

    def speak(self, text: str):
        """播放語音"""
        if not self.enabled or not self.engine:
            return
        
        try:
            print(f"🔊 播放語音: {text}")
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"❌ 語音播放失敗: {e}")

    def alert_strong_breakout(self):
        """有力突破警報"""
        self.speak("有力突破，請睇圖！")

    def alert_fake_breakout(self):
        """虛火假突破警報"""
        self.speak("虛火警報，切勿追高！")

    def alert_custom(self, message: str):
        """自訂警報"""
        self.speak(message)

    def test(self):
        """測試語音"""
        print("🧪 測試語音警報...")
        self.speak("測試語音警報系統")
        self.speak("有力突破，請睇圖！")
        self.speak("虛火警報，切勿追高！")


# 測試函數
def test_voice():
    """測試語音警報"""
    voice = VoiceAlert()
    
    if voice.enabled:
        voice.test()
        print("\n✅ 語音測試完成！")
    else:
        print("\n❌ 語音系統未啟用")


if __name__ == "__main__":
    test_voice()
