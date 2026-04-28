# 🚀 BTC Day Trade 雷達 - 快速啟動指南

## ✅ 系統已設定完成！

你的配置：
- ✅ DeepSeek API：已設定
- ✅ Telegram Bot：已設定
- ✅ Telegram Chat ID：949100281
- ✅ 數據來源：Binance 公開 API（無需帳號）

---

## 🎯 立即開始使用

### 方法 1：一鍵啟動（推薦）

```bash
cd /Users/joeychow/CascadeProjects/windsurf-project/radar_core
python3 public_scanner.py
```

### 方法 2：使用自動重連腳本

```bash
python3 start_radar.py
```

---

## 📱 測試 Telegram 推送

先測試一下 Telegram 是否正常：

```bash
python3 telegram_sender.py
```

你應該會在 Telegram 收到測試訊息！

---

## 🔊 測試語音警報

```bash
python3 voice_alert.py
```

電腦喇叭會播放：「有力突破，請睇圖！」

---

## 📸 測試截圖功能（需要 TradingView URL）

如果你有 TradingView 圖表，可以測試截圖：

```bash
python3 mobile_screenshot.py
```

---

## 🎯 系統運行後會做什麼？

1. **每秒掃描** BTC 市場數據
2. **計算 Vegas 隧道** 和 **CVD 能量**
3. **偵測突破信號**（有力/虛火）
4. **DeepSeek AI 過濾**（信心評分 >= 7 才推送）
5. **觸發警報時**：
   - 🔊 電腦播放語音「有力突破，請睇圖！」
   - 📸 截取 TradingView 圖表（如有設定）
   - 📱 推送到你的 Telegram（含截圖和分析）
   - 📊 發送數據到 n8n（如有設定）

---

## 📊 運行範例

```
🚀 BTC Day Trade 實戰雷達 - 公開 API 版本
============================================================

📊 監控交易對: BTCUSDT
🌐 數據來源: Binance 公開 API（無需帳號）
⏱️  掃描間隔: 1 秒
📈 Vegas 隧道: EMA 144/169
🤖 AI 過濾: 啟用
🔊 語音警報: 啟用
📱 Telegram: 啟用
============================================================

🚀 開始監控 BTC (公開 API)...

[21:00:01] $45,100.00 | Vegas:✅ | CVD:📈0.0500 | OI:1234567890
[21:00:02] $45,120.00 | Vegas:✅ | CVD:📈0.0800 | OI:1234567890
[21:00:03] $45,150.00 | Vegas:✅ | CVD:📈0.1200 | OI:1234567890
...

⚡ 初步偵測到: STRONG
🤖 DeepSeek 分析中...
   信心評分: 9/10
   是否推送: ✅ 是
   分析: CVD 與價格同步創高，真突破機率極高

============================================================
🔔 觸發警報: STRONG
💰 價格: $45,234.50
📊 CVD 斜率: 0.2500
🤖 AI 信心: 9/10
============================================================

🔊 播放語音: 有力突破，請睇圖！
📸 正在截圖...
✅ 截圖成功: screenshots/btc_mobile_20260423_210015.png
📱 推送到 Telegram...
✅ Telegram 警報已發送（含截圖）

✅ 警報處理完成
```

---

## ⚙️ 進階設定（選填）

### 設定 TradingView 圖表 URL

如果你想要自動截圖，編輯 `.env`：

```env
TRADINGVIEW_CHART_URL=https://www.tradingview.com/chart/你的圖表ID/
```

### 設定 n8n Webhook（用於記錄數據到 Google Sheets）

編輯 `.env`：

```env
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/btc-alert
```

### 調整 AI 信心閾值

編輯 `.env`：

```env
DEEPSEEK_CONFIDENCE_THRESHOLD=7  # 改為 8 更嚴格，6 更寬鬆
```

### 調整警報冷卻時間

編輯 `.env`：

```env
ALERT_COOLDOWN=180  # 秒，預設 3 分鐘
```

---

## ❓ 常見問題

### Q: 語音警報沒有聲音？

A: 檢查電腦音量，或在 `.env` 中停用：
```env
VOICE_ALERT_ENABLED=false
```

### Q: 沒有收到 Telegram 訊息？

A: 執行測試：
```bash
python3 telegram_sender.py
```

如果失敗，檢查：
1. Bot Token 是否正確
2. Chat ID 是否正確
3. 是否已與 Bot 對話過（發送 /start）

### Q: DeepSeek API 錯誤？

A: 檢查 API Key 是否正確，或訪問 [https://platform.deepseek.com](https://platform.deepseek.com) 查看配額

### Q: 想停止監控？

A: 按 `Ctrl+C` 即可停止

---

## 🎉 開始使用

現在執行：

```bash
python3 public_scanner.py
```

系統會開始監控 BTC，當偵測到高信心信號時，會自動推送到你的 Telegram！

祝你交易順利！🚀
