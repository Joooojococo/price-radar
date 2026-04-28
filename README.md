# BTC 高頻監控系統 (radar_core)

## 🎯 系統概述

這是一個專業的 BTC 高頻監控系統，每秒掃描 Binance BTC/USDT 市場數據，自動偵測**有力突破**和**虛火假突破**，並在觸發時自動截圖 TradingView 圖表，推送到 n8n 和 Telegram。

### 核心功能

1. **高頻數據採集** - 每秒抓取 Binance 實時數據
2. **Vegas 隧道計算** - EMA 144/169 雙均線系統
3. **CVD 能量分析** - 累計成交量差 + 斜率計算
4. **智能觸發機制** - 有力突破 vs 虛火假突破
5. **自動截圖** - Playwright 自動截取 TradingView 圖表
6. **多渠道推送** - n8n Webhook + Telegram Bot

---

## 🚀 快速開始

### 1. 安裝系統

```bash
cd radar_core
chmod +x setup.sh
./setup.sh
```

這將自動：
- 創建 Python 虛擬環境
- 安裝所有依賴
- 安裝 Playwright 瀏覽器
- 創建必要的目錄
- 複製 .env 範例文件

### 2. 配置環境變數

編輯 `.env` 文件：

```bash
nano .env
```

必填項目：
```env
# Binance API
BINANCE_API_KEY=你的_API_Key
BINANCE_API_SECRET=你的_API_Secret

# n8n Webhook
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/btc-alert

# TradingView 圖表
TRADINGVIEW_CHART_URL=https://www.tradingview.com/chart/你的圖表ID/
```

可選項目：
```env
# Telegram Bot（直接推送截圖）
TELEGRAM_BOT_TOKEN=你的_Bot_Token
TELEGRAM_CHAT_ID=你的_Chat_ID
```

### 3. 測試系統

```bash
./test.sh
```

這將測試：
- ✅ 環境變數配置
- ✅ Telegram Bot 連接
- ✅ 截圖功能
- ✅ Python 依賴

### 4. 啟動監控

```bash
./start.sh
```

系統將開始每秒掃描市場，日誌保存在 `logs/` 目錄。

---

## 📊 監控邏輯

### Vegas 隧道

使用 15 分鐘 K 線計算：
- **EMA 144** - 快速均線
- **EMA 169** - 慢速均線
- **隧道上軌** = max(EMA144, EMA169)

### CVD 能量

計算方式：
```python
CVD = Σ(主動買入量) - Σ(主動賣出量)
```

斜率計算：
- 取過去 5 分鐘的 CVD 數據
- 使用線性回歸計算斜率
- 斜率 > 0.15 表示強勢買盤
- 斜率 < -0.15 表示強勢賣盤

### 觸發機制

#### 🚨 有力突破 (STRONG)

**條件**：
1. 價格突破 Vegas 隧道上軌
2. CVD 斜率 > 0.15（強勢買盤）

**解讀**：
- ✅ 主動買盤強勁
- ✅ 真突破機率高
- ✅ 可考慮做多

#### ⚠️ 虛火假突破 (FAKE)

**條件**：
1. 價格創新高
2. CVD 斜率 < -0.15（買盤枯竭或背離）

**解讀**：
- ⚠️ 主動買盤枯竭
- ⚠️ 假突破警告
- ⚠️ 可能出現天地針

### 冷卻機制

- 相同類型警報間隔 **5 分鐘**（可調整）
- 不同類型警報立即觸發
- 避免重複推送

---

## 📸 截圖功能

### 工作流程

1. 警報觸發
2. Playwright 啟動無頭瀏覽器
3. 訪問 TradingView 圖表
4. 等待 3 秒載入
5. 自動關閉彈窗
6. 截取全屏圖表
7. 保存到 `screenshots/` 目錄

### 截圖設定

編輯 `screenshot_handler.py`：

```python
self.viewport_width = 1920   # 寬度
self.viewport_height = 1080  # 高度
self.wait_time = 3           # 等待時間（秒）
```

### 清理舊截圖

```python
# 保留最近 7 天的截圖
handler.cleanup_old_screenshots(days=7)
```

---

## 📱 推送渠道

### 1. n8n Webhook

**數據格式**：
```json
{
  "type": "STRONG",
  "symbol": "BTCUSDT",
  "price": 45234.50,
  "timestamp": "2026-04-23T20:00:00",
  "vegas": {
    "ema_fast": 45100.00,
    "ema_slow": 45050.00,
    "upper": 45100.00
  },
  "cvd_slope": 0.25,
  "open_interest": 1234567890.0,
  "screenshot_path": "screenshots/btc_chart_20260423_200000.png",
  "telegram_file_id": "AgACAgUAAxkBAAI...",
  "message": "🚨 有力突破警報\n..."
}
```

### 2. Telegram Bot

**功能**：
- 直接發送警報訊息
- 附帶截圖
- 減輕 n8n 處理大文件壓力

**訊息格式**：
```
🚨 有力突破 警報

【交易對】BTCUSDT
【價格】$45,234.50
【CVD 斜率】0.2500
【時間】2026-04-23 20:00:00

【解讀】
✅ 價格突破 Vegas 隧道
✅ CVD 同步強勢創高
✅ 主動買盤強勁，真突破機率高

【操作建議】
進場機會，可考慮做多
止損設於 Vegas 下軌
```

---

## 🔧 進階配置

### 調整掃描間隔

編輯 `.env`：
```env
SCAN_INTERVAL=1  # 改為 2 = 每 2 秒掃描一次
```

### 調整 CVD 參數

編輯 `.env`：
```env
CVD_LOOKBACK_MINUTES=5      # CVD 回溯時間（分鐘）
CVD_SLOPE_THRESHOLD=0.15    # 斜率閾值
```

### 調整 Vegas 參數

編輯 `.env`：
```env
EMA_FAST=144  # 快速均線
EMA_SLOW=169  # 慢速均線
```

### 調整警報冷卻

編輯 `.env`：
```env
ALERT_COOLDOWN=300  # 改為 180 = 3 分鐘
```

---

## 📁 文件結構

```
radar_core/
├── scanner.py              # 主掃描器
├── screenshot_handler.py   # 截圖處理器
├── telegram_sender.py      # Telegram 發送器
├── requirements.txt        # Python 依賴
├── .env.example           # 環境變數範例
├── .env                   # 環境變數（需自行創建）
├── setup.sh               # 安裝腳本
├── start.sh               # 啟動腳本
├── test.sh                # 測試腳本
├── README.md              # 本文件
├── screenshots/           # 截圖保存目錄
├── logs/                  # 日誌保存目錄
└── venv/                  # Python 虛擬環境
```

---

## 🧪 測試指令

### 測試 Telegram Bot

```bash
source venv/bin/activate
python3 telegram_sender.py
```

### 測試截圖功能

```bash
source venv/bin/activate
python3 screenshot_handler.py
```

### 測試完整系統

```bash
./test.sh
```

---

## 📊 實戰案例

### 案例 1: 有力突破

```
[20:15:30] 價格: $45,234.50 | Vegas: ✅ | CVD: 📈 0.2500 | OI: 1234567890

🔔 偵測到突破: STRONG

🚨 有力突破 警報

【交易對】BTCUSDT
【價格】$45,234.50
【CVD 斜率】0.2500
【時間】2026-04-23 20:15:30

📸 正在截圖 TradingView 圖表...
✅ 截圖完成: screenshots/btc_chart_20260423_201530.png
✅ 警報已發送到 n8n: STRONG
✅ Telegram 警報已發送（含截圖）
```

### 案例 2: 虛火假突破

```
[20:45:15] 價格: $46,800.00 | Vegas: ✅ | CVD: 📉 -0.1800 | OI: 1234567890

🔔 偵測到突破: FAKE

⚠️ 虛火假突破 警報

【交易對】BTCUSDT
【價格】$46,800.00
【CVD 斜率】-0.1800
【時間】2026-04-23 20:45:15

📸 正在截圖 TradingView 圖表...
✅ 截圖完成: screenshots/btc_chart_20260423_204515.png
✅ 警報已發送到 n8n: FAKE
✅ Telegram 警報已發送（含截圖）
```

---

## ⚠️ 注意事項

### 1. Binance API

- 需要有效的 API Key 和 Secret
- 建議開啟 IP 白名單
- 現貨交易對無法獲取 OI（持倉量）
- 如需 OI，請使用合約 API

### 2. TradingView 圖表

- 確保圖表 URL 可公開訪問
- 建議使用已登入的圖表（更穩定）
- 首次截圖可能較慢（載入瀏覽器）

### 3. 系統資源

- 每秒掃描會持續使用 API 配額
- 截圖需要 Chromium 瀏覽器（約 300MB）
- 建議至少 1GB RAM

### 4. 網絡要求

- 需要穩定的網絡連接
- 訪問 Binance API
- 訪問 TradingView
- 訪問 n8n Webhook
- 訪問 Telegram API

---

## 🔍 故障排除

### 問題 1: 無法連接 Binance

**解決方案**：
- 檢查 API Key 是否正確
- 檢查網絡連接
- 檢查 IP 是否在白名單

### 問題 2: 截圖失敗

**解決方案**：
```bash
# 重新安裝 Playwright 瀏覽器
playwright install chromium

# 檢查 TradingView URL 是否正確
echo $TRADINGVIEW_CHART_URL
```

### 問題 3: Telegram 發送失敗

**解決方案**：
- 檢查 Bot Token 是否正確
- 檢查 Chat ID 是否正確
- 確認已與 Bot 對話過（發送 /start）

### 問題 4: n8n 未收到數據

**解決方案**：
- 檢查 Webhook URL 是否正確
- 測試 Webhook：
```bash
curl -X POST $N8N_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

---

## 📈 效能優化

### 1. 減少 API 調用

```python
# 調整掃描間隔
SCAN_INTERVAL=2  # 從 1 秒改為 2 秒
```

### 2. 優化截圖速度

```python
# 減少等待時間
self.wait_time = 2  # 從 3 秒改為 2 秒
```

### 3. 清理舊數據

```bash
# 定期清理舊截圖
find screenshots/ -name "*.png" -mtime +7 -delete
```

---

## 🚀 未來增強

- [ ] 支援多交易對監控
- [ ] 整合更多技術指標
- [ ] 機器學習信號優化
- [ ] Web 儀表板
- [ ] 歷史回測功能
- [ ] 自動交易整合

---

**開發者**: 專為高頻交易者打造
**版本**: 1.0.0
**技術**: Python + Binance API + Playwright + Telegram
