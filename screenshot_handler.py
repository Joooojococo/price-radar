#!/usr/bin/env python3
"""
截圖處理器
使用 Playwright 自動截取 TradingView 圖表
"""

import os
import asyncio
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()


class ScreenshotHandler:
    def __init__(self):
        """初始化截圖處理器"""
        self.chart_url = os.getenv('TRADINGVIEW_CHART_URL')
        self.screenshot_dir = Path('screenshots')
        self.screenshot_dir.mkdir(exist_ok=True)
        
        # 瀏覽器設定
        self.viewport_width = 1920
        self.viewport_height = 1080
        self.wait_time = 3  # 等待圖表載入的時間（秒）
        
        print(f"📸 截圖處理器初始化完成")
        print(f"📂 截圖保存目錄: {self.screenshot_dir.absolute()}")

    async def capture_chart(self) -> str:
        """
        截取 TradingView 圖表
        返回: 截圖文件路徑
        """
        if not self.chart_url:
            print("⚠️  未設定 TRADINGVIEW_CHART_URL，跳過截圖")
            return None
        
        try:
            async with async_playwright() as p:
                # 啟動瀏覽器（無頭模式）
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                # 創建頁面
                page = await browser.new_page(
                    viewport={'width': self.viewport_width, 'height': self.viewport_height}
                )
                
                # 訪問圖表
                print(f"🌐 正在載入圖表: {self.chart_url}")
                await page.goto(self.chart_url, wait_until='networkidle')
                
                # 等待圖表完全載入
                await asyncio.sleep(self.wait_time)
                
                # 嘗試關閉可能的彈窗
                try:
                    # 關閉登入提示
                    await page.click('button[aria-label="Close"]', timeout=2000)
                except:
                    pass
                
                try:
                    # 關閉廣告
                    await page.click('.tv-dialog__close', timeout=2000)
                except:
                    pass
                
                # 生成文件名
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'btc_chart_{timestamp}.png'
                filepath = self.screenshot_dir / filename
                
                # 截圖
                await page.screenshot(
                    path=str(filepath),
                    full_page=False,
                    type='png'
                )
                
                # 關閉瀏覽器
                await browser.close()
                
                print(f"✅ 截圖成功: {filepath}")
                return str(filepath)
                
        except Exception as e:
            print(f"❌ 截圖失敗: {e}")
            return None

    async def capture_chart_with_selector(self, selector: str = None) -> str:
        """
        截取圖表的特定區域
        selector: CSS 選擇器，例如 '.chart-container'
        """
        if not self.chart_url:
            return None
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(
                    viewport={'width': self.viewport_width, 'height': self.viewport_height}
                )
                
                await page.goto(self.chart_url, wait_until='networkidle')
                await asyncio.sleep(self.wait_time)
                
                # 關閉彈窗
                try:
                    await page.click('button[aria-label="Close"]', timeout=2000)
                except:
                    pass
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'btc_chart_{timestamp}.png'
                filepath = self.screenshot_dir / filename
                
                if selector:
                    # 截取特定元素
                    element = await page.query_selector(selector)
                    if element:
                        await element.screenshot(path=str(filepath))
                    else:
                        await page.screenshot(path=str(filepath))
                else:
                    await page.screenshot(path=str(filepath))
                
                await browser.close()
                
                print(f"✅ 截圖成功: {filepath}")
                return str(filepath)
                
        except Exception as e:
            print(f"❌ 截圖失敗: {e}")
            return None

    def cleanup_old_screenshots(self, days: int = 7):
        """清理舊截圖（保留最近 N 天）"""
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
async def test_screenshot():
    """測試截圖功能"""
    handler = ScreenshotHandler()
    screenshot_path = await handler.capture_chart()
    
    if screenshot_path:
        print(f"\n✅ 測試成功！")
        print(f"📸 截圖位置: {screenshot_path}")
    else:
        print(f"\n❌ 測試失敗")


if __name__ == "__main__":
    asyncio.run(test_screenshot())
