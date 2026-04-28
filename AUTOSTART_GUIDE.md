# 🚀 BTC 雷達開機自動啟動指南

## 📋 功能說明

設定後，每次開機或登入 macOS 時，BTC 雷達會自動在背景啟動，無需手動執行。

---

## ✅ 安裝開機自動啟動

### 方法 1：一鍵安裝（推薦）

```bash
cd /Users/joeychow/CascadeProjects/windsurf-project/radar_core
./install_autostart.sh
```

### 方法 2：手動安裝

```bash
# 1. 複製配置文件
cp com.btc.radar.plist ~/Library/LaunchAgents/

# 2. 載入服務
launchctl load ~/Library/LaunchAgents/com.btc.radar.plist
```

---

## 🔍 驗證是否成功

### 檢查服務狀態

```bash
launchctl list | grep btc.radar
```

如果看到類似這樣的輸出，表示成功：
```
12345  0  com.btc.radar
```

### 查看運行日誌

```bash
tail -f logs/radar.log
```

你應該會看到雷達正在監控 BTC 的即時數據。

---

## 🎯 系統行為

### 開機後會自動：

1. ✅ 啟動 BTC 雷達
2. ✅ 連接 Binance API
3. ✅ 啟用 DeepSeek AI 分析
4. ✅ 連接 Telegram Bot
5. ✅ 開始每秒監控 BTC

### 如果雷達崩潰：

- ✅ **自動重啟**（KeepAlive 功能）
- ✅ 錯誤會記錄到 `logs/radar_error.log`

---

## 📊 管理指令

### 停止雷達

```bash
launchctl unload ~/Library/LaunchAgents/com.btc.radar.plist
```

### 啟動雷達

```bash
launchctl load ~/Library/LaunchAgents/com.btc.radar.plist
```

### 重啟雷達

```bash
launchctl unload ~/Library/LaunchAgents/com.btc.radar.plist
launchctl load ~/Library/LaunchAgents/com.btc.radar.plist
```

### 查看即時日誌

```bash
# 查看正常日誌
tail -f logs/radar.log

# 查看錯誤日誌
tail -f logs/radar_error.log
```

---

## 🛑 移除開機自動啟動

### 方法 1：一鍵移除（推薦）

```bash
./uninstall_autostart.sh
```

### 方法 2：手動移除

```bash
# 1. 卸載服務
launchctl unload ~/Library/LaunchAgents/com.btc.radar.plist

# 2. 刪除配置文件
rm ~/Library/LaunchAgents/com.btc.radar.plist
```

---

## 📁 文件位置

### 配置文件
```
~/Library/LaunchAgents/com.btc.radar.plist
```

### 日誌文件
```
/Users/joeychow/CascadeProjects/windsurf-project/radar_core/logs/radar.log
/Users/joeychow/CascadeProjects/windsurf-project/radar_core/logs/radar_error.log
```

### 雷達程式
```
/Users/joeychow/CascadeProjects/windsurf-project/radar_core/simple_scanner.py
```

---

## ⚙️ 進階設定

### 修改配置

編輯 `com.btc.radar.plist`：

```xml
<!-- 修改工作目錄 -->
<key>WorkingDirectory</key>
<string>/你的/路徑</string>

<!-- 修改日誌位置 -->
<key>StandardOutPath</key>
<string>/你的/日誌/路徑.log</string>

<!-- 停用自動重啟 -->
<key>KeepAlive</key>
<false/>
```

修改後重新載入：
```bash
launchctl unload ~/Library/LaunchAgents/com.btc.radar.plist
launchctl load ~/Library/LaunchAgents/com.btc.radar.plist
```

---

## ❓ 常見問題

### Q: 開機後沒有自動啟動？

A: 檢查：
1. 配置文件是否存在：`ls ~/Library/LaunchAgents/com.btc.radar.plist`
2. 服務是否載入：`launchctl list | grep btc.radar`
3. 查看錯誤日誌：`cat logs/radar_error.log`

### Q: 如何確認雷達正在運行？

A: 執行：
```bash
# 方法 1：查看進程
ps aux | grep simple_scanner.py

# 方法 2：查看日誌
tail logs/radar.log
```

### Q: 想暫時停止但不移除？

A: 執行：
```bash
launchctl unload ~/Library/LaunchAgents/com.btc.radar.plist
```

要重新啟動時：
```bash
launchctl load ~/Library/LaunchAgents/com.btc.radar.plist
```

### Q: 如何更新雷達程式？

A: 更新程式碼後，重啟服務：
```bash
launchctl unload ~/Library/LaunchAgents/com.btc.radar.plist
launchctl load ~/Library/LaunchAgents/com.btc.radar.plist
```

---

## 🎯 測試開機自動啟動

### 方法 1：登出再登入

```bash
# 登出
# 重新登入
# 檢查雷達是否運行
launchctl list | grep btc.radar
```

### 方法 2：重啟電腦

```bash
# 重啟電腦
# 開機後檢查
tail -f logs/radar.log
```

---

## 📱 確認推送正常

開機後，雷達會自動發送一條測試訊息到你的 Telegram（可選）。

如果沒收到，檢查：
1. `.env` 文件是否正確
2. Telegram Bot Token 是否有效
3. 查看錯誤日誌

---

## 🚀 完成！

設定完成後，你的 BTC 雷達會：

✅ 開機自動啟動  
✅ 背景持續運行  
✅ 自動重啟（如果崩潰）  
✅ 記錄所有日誌  
✅ 推送警報到 Telegram  

**完全自動化，無需人工干預！** 🎉
