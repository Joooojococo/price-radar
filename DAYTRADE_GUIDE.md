# BTC Day Trade 實戰雷達 - 極速版使用指南

## 🎯 系統特色

這是一個專為 **Day Trade** 打造的極速 BTC 監控系統，整合：

1. **🤖 DeepSeek AI 語義化過濾** - 過濾洗盤雜訊，只推送高信心信號
2. **🔊 本地語音警報** - 電腦喇叭直接播放「有力突破，請睇圖！」
3. **📱 手機優化截圖** - 800x1200 直向截圖，適合手機查看
4. **⚡ 極速推送** - Telegram 直接推送，不經 n8n，追求秒速
5. **📊 自動數據記錄** - 推送後發送到 n8n，存入 Google Sheets 供復盤
6. **🔄 自動斷線重連** - 網絡中斷自動恢復，無需人工干預

---

## 🚀 快速開始

### 1. 安裝系統

```bash
cd radar_core
./setup.sh
```

### 2. 配置 API

編輯 `.env` 文件：

```env
# Binance API（必填）
BINANCE_API_KEY=你的_API_Key
BINANCE_API_SECRET=你的_API_Secret

# DeepSeek API（必填，用於 AI 過濾）
DEEPSEEK_API_KEY=你的_DeepSeek_Key

# Telegram Bot（必填，極速推送）
TELEGRAM_BOT_TOKEN=你的_Bot_Token
TELEGRAM_CHAT_ID=你的_Chat_ID

# n8n Webhook（選填，數據記錄）
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/btc-alert

# TradingView 圖表（必填）
TRADINGVIEW_CHART_URL=https://www.tradingview.com/chart/你的圖表ID/
```

### 3. 一鍵啟動

**macOS/Linux**:
```bash
./start_radar.sh
```

**Windows**:
```bash
start_radar.bat
```

**或直接執行 Python**:
```bash
python3 start_radar.py
```

---

## 🎯 工作流程

### 完整流程圖

```
每秒掃描市場
    ↓
獲取價格、CVD、OI 數據
    ↓
計算 Vegas 隧道、CVD 斜率
    ↓
偵測突破信號（有力/虛火）
    ↓
快速過濾（CVD 斜率、Vegas 位置）
    ↓
DeepSeek AI 語義化分析
    ↓
信心評分 >= 7？
    ↓ 是
【極速響應】
    ↓
1. 本地語音警報（0.1 秒）
    ↓
2. 截取 TradingView 圖表（3 秒）
    ↓
3. 推送到 Telegram（1 秒）
    ↓
4. 發送數據到 n8n（1 秒）
    ↓
完成（總耗時 < 6 秒）
```

---

## 🤖 DeepSeek AI 過濾

### 為什麼需要 AI 過濾？

傳統技術指標容易產生**洗盤雜訊**：
- ❌ 價格突破但 CVD 背離（假突破）
- ❌ 短暫的量能異常（洗盤）
- ❌ OI 變化但無實質意義

DeepSeek AI 可以：
- ✅ 理解 CVD/OI 數據的語義
- ✅ 判斷突破的真實性
- ✅ 給出 1-10 的信心評分
- ✅ 過濾低於 7 分的雜訊信號

### AI 分析範例

**輸入數據**:
```json
{
  "signal_type": "STRONG",
  "current_price": 45234.50,
  "cvd_history": [100, 105, 110, 115, 120, ...],
  "oi_history": [1000000, 1010000, 1020000, ...],
  "vegas_position": "突破上軌"
}
```

**AI 回應**:
```json
{
  "confidence": 9,
  "should_alert": true,
  "analysis": "CVD 與價格同步創高，OI 穩定增加，真突破機率極高",
  "reason": "能量與價格共振"
}
```

**結果**: ✅ 推送警報

---

**輸入數據**:
```json
{
  "signal_type": "STRONG",
  "current_price": 45500.00,
  "cvd_history": [100, 102, 101, 99, 98, ...],
  "oi_history": [1000000, 999000, 998000, ...],
  "vegas_position": "突破上軌"
}
```

**AI 回應**:
```json
{
  "confidence": 3,
  "should_alert": false,
  "analysis": "價格創高但 CVD 走平，OI 下降，疑似洗盤雜訊",
  "reason": "能量背離"
}
```

**結果**: ❌ 靜默（不推送）

---

## 🔊 語音警報

### 功能

當信號觸發時，電腦喇叭會立即播放：

- **有力突破**: 「有力突破，請睇圖！」
- **虛火假突破**: 「虛火警報，切勿追高！」

### 優勢

- ⚡ **極速** - 本地播放，延遲 < 0.1 秒
- 🔔 **提醒** - 即使不看螢幕也能收到警報
- 🎯 **專注** - 不用一直盯盤

### 測試語音

```bash
python3 voice_alert.py
```

### 停用語音

編輯 `.env`:
```env
VOICE_ALERT_ENABLED=false
```

---

## 📱 手機優化截圖

### 特色

- **直向尺寸**: 800x1200（適合手機查看）
- **自動隱藏 UI**: 執行 ALT+H 隱藏雜圖
- **高清截圖**: PNG 格式，清晰度高

### 截圖範例

```
截圖前（雜亂）:
┌─────────────────┐
│ TradingView UI  │
│ 廣告、工具列等   │
│                 │
│   圖表區域      │
│                 │
└─────────────────┘

截圖後（乾淨）:
┌─────────────────┐
│                 │
│                 │
│   純圖表        │
│   800x1200      │
│                 │
│                 │
└─────────────────┘
```

### 測試截圖

```bash
python3 mobile_screenshot.py
```

---

## ⚡ 極速推送流程

### 傳統流程（慢）

```
信號觸發
  ↓
發送到 n8n
  ↓
n8n 處理截圖
  ↓
n8n 推送到 Telegram
  ↓
總耗時: 10-15 秒
```

### 極速流程（快）

```
信號觸發
  ↓
本地語音警報（0.1 秒）
  ↓
本地截圖（3 秒）
  ↓
直接推送到 Telegram（1 秒）
  ↓
總耗時: < 5 秒
```

### 數據記錄

推送完成後，再發送純文字數據到 n8n：

```json
{
  "type": "STRONG",
  "price": 45234.50,
  "cvd_slope": 0.25,
  "ai_confidence": 9,
  "ai_analysis": "CVD 與價格同步創高...",
  "timestamp": "2026-04-23T21:00:00"
}
```

n8n 可以將這些數據存入 Google Sheets 供日後復盤。

---

## 🔄 自動斷線重連

### 功能

- ✅ 網絡中斷自動重連
- ✅ API 錯誤自動重試
- ✅ 連續錯誤等待 30 秒
- ✅ 無限重試，無需人工干預

### 重連邏輯

```python
while True:
    try:
        # 掃描市場
        scan_market()
    except NetworkError:
        print("⚠️  網絡中斷，10 秒後重試...")
        time.sleep(10)
        continue
    except APIError:
        print("⚠️  API 錯誤，10 秒後重試...")
        time.sleep(10)
        continue
```

### 日誌範例

```
[21:00:00] $45,100.00 | Vegas:✅ | CVD:📈0.0500
[21:00:01] $45,120.00 | Vegas:✅ | CVD:📈0.0800
❌ 網絡中斷，10 秒後重試...
[21:00:11] 重新連接中...
✅ 連接成功
[21:00:12] $45,150.00 | Vegas:✅ | CVD:📈0.1200
```

---

## 📊 實戰案例

### 案例 1: 有力突破（AI 信心 9/10）

```
[21:15:30] $45,234.50 | Vegas:✅ | CVD:📈0.2500

⚡ 初步偵測到: STRONG
🤖 DeepSeek 分析中...
   信心評分: 9/10
   是否推送: ✅ 是
   分析: CVD 與價格同步創高，OI 穩定增加，真突破機率極高

🔔 觸發警報: STRONG
💰 價格: $45,234.50
📊 CVD 斜率: 0.2500
🤖 AI 信心: 9/10

🔊 播放語音: 有力突破，請睇圖！
📸 正在截圖...
✅ 截圖成功: screenshots/btc_mobile_20260423_211530.png
📱 推送到 Telegram...
✅ Telegram 警報已發送（含截圖）
📊 發送數據到 n8n...
✅ 數據已發送到 n8n

✅ 警報處理完成（總耗時: 4.8 秒）
```

**Telegram 收到**:
```
🚨 有力突破 警報

【交易對】BTCUSDT
【價格】$45,234.50
【時間】21:15:30

【技術指標】
• CVD 斜率: 0.2500
• Vegas 上軌: $45,100.00
• OI: 1,234,567,890

【AI 分析】
• 信心評分: 9/10
• 分析: CVD 與價格同步創高，OI 穩定增加，真突破機率極高
• 理由: 能量與價格共振

【操作建議】
✅ 進場機會，可考慮做多
⚠️ 止損設於 Vegas 下軌
📈 目標看高一檔

[附帶 800x1200 截圖]
```

---

### 案例 2: 虛火假突破（AI 信心 3/10，靜默）

```
[21:45:15] $46,800.00 | Vegas:✅ | CVD:📉-0.1800

⚡ 初步偵測到: FAKE
🤖 DeepSeek 分析中...
   信心評分: 3/10
   是否推送: ❌ 否（洗盤雜訊）
   分析: 價格創高但 CVD 走平，OI 下降，疑似洗盤雜訊

❌ AI 判定為洗盤雜訊（信心: 3/10），靜默

[21:45:16] $46,750.00 | Vegas:✅ | CVD:📉-0.1900
```

**結果**: 不推送，避免誤報

---

## 🔧 參數調整

### 調整 AI 信心閾值

編輯 `.env`:
```env
# 預設 7，改為 8 更嚴格
DEEPSEEK_CONFIDENCE_THRESHOLD=8

# 改為 6 更寬鬆
DEEPSEEK_CONFIDENCE_THRESHOLD=6
```

### 調整警報冷卻

```env
# 預設 180 秒（3 分鐘）
ALERT_COOLDOWN=180

# 改為 120 秒（2 分鐘）
ALERT_COOLDOWN=120
```

### 調整 CVD 閾值

```env
# 預設 0.15
CVD_SLOPE_THRESHOLD=0.15

# 改為 0.20 更嚴格
CVD_SLOPE_THRESHOLD=0.20
```

### 調整截圖尺寸

```env
# 預設 800x1200（手機直向）
SCREENSHOT_WIDTH=800
SCREENSHOT_HEIGHT=1200

# 改為 1080x1920（更大）
SCREENSHOT_WIDTH=1080
SCREENSHOT_HEIGHT=1920
```

---

## 📁 文件結構

```
radar_core/
├── daytrade_scanner.py       # 主掃描器（整合版）
├── deepseek_analyzer.py      # DeepSeek AI 分析器
├── voice_alert.py            # 語音警報系統
├── mobile_screenshot.py      # 手機優化截圖
├── telegram_sender.py        # Telegram 發送器
├── start_radar.py            # 自動啟動腳本（Python）
├── start_radar.sh            # 自動啟動腳本（Shell）
├── start_radar.bat           # 自動啟動腳本（Windows）
├── requirements.txt          # Python 依賴
├── .env.example             # 環境變數範例
├── .env                     # 環境變數（需自行創建）
├── setup.sh                 # 安裝腳本
├── test.sh                  # 測試腳本
├── screenshots/             # 截圖保存目錄
└── logs/                    # 日誌保存目錄
```

---

## 🧪 測試指令

### 測試 DeepSeek AI

```bash
python3 deepseek_analyzer.py
```

### 測試語音警報

```bash
python3 voice_alert.py
```

### 測試截圖功能

```bash
python3 mobile_screenshot.py
```

### 測試 Telegram

```bash
python3 telegram_sender.py
```

### 測試完整系統

```bash
./test.sh
```

---

## ⚠️ 注意事項

### 1. DeepSeek API

- 需要有效的 API Key
- 每次分析消耗約 500 tokens
- 建議開啟 API 使用監控

### 2. 語音警報

- macOS 內建中文語音
- Windows 需安裝中文語音包
- Linux 可能需要額外配置

### 3. 截圖功能

- 需要 ChromeDriver（自動下載）
- 首次截圖較慢（載入瀏覽器）
- 建議保持 TradingView 圖表打開

### 4. 系統資源

- 每秒掃描會持續使用 CPU
- DeepSeek API 調用需要網絡
- 建議至少 2GB RAM

---

## 🎯 最佳實踐

### 1. 每晚開工流程

```bash
# 1. 打開 TradingView 圖表
# 2. 啟動雷達
./start_radar.sh

# 3. 等待警報
# 系統會自動監控，無需人工干預
```

### 2. 收到警報後

```
1. 聽到語音「有力突破，請睇圖！」
2. 查看 Telegram 推送（含截圖）
3. 檢查 AI 信心評分
4. 如果 >= 8 分，考慮進場
5. 如果 < 7 分，謹慎觀望
```

### 3. 復盤流程

```
1. 打開 Google Sheets（n8n 自動記錄）
2. 查看歷史警報數據
3. 統計 AI 信心評分 vs 實際結果
4. 調整參數優化系統
```

---

## 🚀 未來增強

- [ ] 支援多交易對監控
- [ ] 整合更多 AI 模型（GPT-4, Claude）
- [ ] 自動交易整合
- [ ] Web 儀表板
- [ ] 移動端 App

---

**開發者**: 專為 Day Trader 打造的極速雷達
**版本**: 2.0.0 - 極速版
**技術**: Python + Binance + DeepSeek AI + Selenium + Telegram
