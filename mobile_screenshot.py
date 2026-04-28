#!/usr/bin/env python3
"""
手機優化截圖處理器
使用 Selenium 截取 800x1200 直向圖表
自動執行 ALT+H 隱藏 UI
"""

import os
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

load_dotenv()


class MobileScreenshot:
    def __init__(self):
        """初始化手機優化截圖處理器"""
        self.chart_url = os.getenv('TRADINGVIEW_CHART_URL')
        self.screenshot_dir = Path('screenshots')
        self.screenshot_dir.mkdir(exist_ok=True)
        
        # 手機直向尺寸
        self.width = int(os.getenv('SCREENSHOT_WIDTH', 800))
        self.height = int(os.getenv('SCREENSHOT_HEIGHT', 1200))
        self.hide_ui = os.getenv('SCREENSHOT_HIDE_UI', 'true').lower() == 'true'
        
        # 等待時間
        self.wait_time = 3
        
        print(f"📱 手機截圖處理器初始化完成")
        print(f"📐 截圖尺寸: {self.width}x{self.height} (直向)")
        print(f"🎨 隱藏 UI: {'是' if self.hide_ui else '否'}")

    def setup_driver(self):
        """設定 Chrome WebDriver"""
        if not SELENIUM_AVAILABLE:
            raise RuntimeError("selenium 未安裝，請執行: pip install selenium webdriver-manager")
        chrome_options = Options()
        
        # 無頭模式（背景運行）
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        # 設定視窗大小（手機直向）
        chrome_options.add_argument(f'--window-size={self.width},{self.height}')
        
        # 禁用通知
        chrome_options.add_argument('--disable-notifications')
        
        # 自動下載 ChromeDriver
        service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_window_size(self.width, self.height)
        
        return driver

    def capture_chart(self) -> str:
        """
        截取 TradingView 圖表（手機優化）
        返回: 截圖文件路徑
        """
        if not self.chart_url:
            print("⚠️  未設定 TRADINGVIEW_CHART_URL，跳過截圖")
            return None
        
        driver = None
        try:
            print(f"🌐 正在載入圖表: {self.chart_url}")
            
            # 啟動瀏覽器
            driver = self.setup_driver()
            
            # 訪問圖表
            driver.get(self.chart_url)
            
            # 等待載入
            time.sleep(self.wait_time)
            
            # 關閉可能的彈窗
            try:
                # 關閉登入提示
                close_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[aria-label="Close"]')
                for btn in close_buttons:
                    try:
                        btn.click()
                        time.sleep(0.5)
                    except:
                        pass
            except:
                pass
            
            try:
                # 關閉廣告
                close_buttons = driver.find_elements(By.CSS_SELECTOR, '.tv-dialog__close')
                for btn in close_buttons:
                    try:
                        btn.click()
                        time.sleep(0.5)
                    except:
                        pass
            except:
                pass
            
            # 隱藏 UI（按 ALT+H）
            if self.hide_ui:
                try:
                    print("🎨 執行 ALT+H 隱藏 UI...")
                    body = driver.find_element(By.TAG_NAME, 'body')
                    
                    # 使用 ActionChains 模擬按鍵
                    actions = ActionChains(driver)
                    actions.key_down(Keys.ALT).send_keys('h').key_up(Keys.ALT).perform()
                    
                    time.sleep(1)
                except Exception as e:
                    print(f"⚠️  隱藏 UI 失敗: {e}")
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'btc_mobile_{timestamp}.png'
            filepath = self.screenshot_dir / filename
            
            # 截圖
            driver.save_screenshot(str(filepath))
            
            print(f"✅ 截圖成功: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            print(f"❌ 截圖失敗: {e}")
            return None
            
        finally:
            if driver:
                driver.quit()

    def capture_chart_fast(self) -> str:
        """
        快速截圖（不啟動瀏覽器）
        使用 pyautogui 直接截取當前螢幕
        適合已經打開 TradingView 的情況
        """
        if not PYAUTOGUI_AVAILABLE:
            print("⚠️  pyautogui 未安裝，跳過快速截圖")
            return None
        try:
            print("⚡ 快速截圖模式...")
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'btc_fast_{timestamp}.png'
            filepath = self.screenshot_dir / filename
            
            # 截取螢幕
            screenshot = pyautogui.screenshot()
            
            # 調整為手機尺寸（裁切中間部分）
            width, height = screenshot.size
            left = (width - self.width) // 2
            top = (height - self.height) // 2
            right = left + self.width
            bottom = top + self.height
            
            cropped = screenshot.crop((left, top, right, bottom))
            cropped.save(str(filepath))
            
            print(f"✅ 快速截圖成功: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            print(f"❌ 快速截圖失敗: {e}")
            return None

    def cleanup_old_screenshots(self, days: int = 7):
        """清理舊截圖"""
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            deleted_count = 0
            for file in self.screenshot_dir.glob('*.png'):
                if file.stat().st_mtime < cutoff_time:
                    file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                print(f"🗑️  已清理 {deleted_count} 個舊截圖")
                
        except Exception as e:
            print(f"❌ 清理截圖失敗: {e}")


# 測試函數
def test_screenshot():
    """測試截圖功能"""
    handler = MobileScreenshot()
    
    print("\n🧪 測試 1: Selenium 截圖（需要 TradingView URL）")
    screenshot_path = handler.capture_chart()
    
    if screenshot_path:
        print(f"✅ Selenium 截圖成功: {screenshot_path}")
    else:
        print(f"❌ Selenium 截圖失敗")
    
    print("\n🧪 測試 2: 快速截圖（截取當前螢幕）")
    fast_path = handler.capture_chart_fast()
    
    if fast_path:
        print(f"✅ 快速截圖成功: {fast_path}")
    else:
        print(f"❌ 快速截圖失敗")


if __name__ == "__main__":
    test_screenshot()
