#!/usr/bin/env python3
"""
ICT + Gann + Candlestick Strategy Scanner
三層入場條件：Gann磁吸位 + 15min趨勢 + K線反轉形態
目標：每天 3-5 次交易機會
"""

import asyncio
import os
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dotenv import load_dotenv

from telegram_sender import TelegramSender

load_dotenv()


class ICTGannScanner:
    """
    三層入場系統：
    第一層：Gann 磁吸位 (±0.5%)
    第二層：15min 趨勢方向 (HH/HL vs LH/LL)
    第三層：K線反轉形態 (6個)
    額外：BB突破加持 = 超強信號
    """

    PATTERN_NAMES = {
        'HAMMER':             '錘頭線',
        'BULLISH_ENGULFING':  '看漲吞沒',
        'MORNING_STAR':       '晨星',
        'SHOOTING_STAR':      '流星線',
        'BEARISH_ENGULFING':  '看跌吞沒',
        'EVENING_STAR':       '黃昏星',
    }

    def __init__(self):
        self.symbol           = os.getenv('SYMBOL', 'BTCUSDT')
        self.scan_interval    = int(float(os.getenv('SCAN_INTERVAL', 60)))
        self.alert_cooldown   = int(float(os.getenv('ALERT_COOLDOWN', 900)))
        self.trend_lookback   = int(float(os.getenv('TREND_LOOKBACK', 16)))
        self.ultra_only       = os.getenv('ULTRA_STRONG_ONLY', 'false').lower() == 'true'

        # Gann tolerance: ±0.5% 或 ±$250 取較大值（可在 .env 覆寫）
        self.gann_tol_pct     = float(os.getenv('GANN_TOLERANCE_PCT', 0.005))
        self.gann_tol_min     = float(os.getenv('GANN_TOLERANCE_MIN', 250))
        self.gann_step        = int(os.getenv('GANN_STEP', 5))  # sqrt step: 5 → ~$2700 gap at $77k

        # Bollinger Bands
        self.bb_period = 20
        self.bb_std    = 2.0

        # Telegram
        self.telegram = TelegramSender()

        # State
        self.last_alert_time = None
        self.last_alert_key  = None

        print(f"{'='*60}")
        print(f"  ICT + Gann + Candlestick Scanner")
        print(f"  交易對: {self.symbol}")
        print(f"  掃描間隔: {self.scan_interval}s | 冷卻: {self.alert_cooldown}s")
        print(f"  趨勢回望: {self.trend_lookback} 根 15min K線")
        print(f"  Gann容差: ±{self.gann_tol_pct*100}% 或 ±${self.gann_tol_min}")
        if self.ultra_only:
            print(f"  模式: 僅超強信號 (BB突破)")
        print(f"{'='*60}\n")

    # ══════════════════════════════════════════════
    # DATA FETCHING
    # ══════════════════════════════════════════════

    def fetch_klines(self, interval: str = '15m', limit: int = 120) -> Optional[pd.DataFrame]:
        """從 Binance Futures 公開 API 獲取 K 線"""
        try:
            r = requests.get(
                'https://fapi.binance.com/fapi/v1/klines',
                params={'symbol': self.symbol, 'interval': interval, 'limit': limit},
                timeout=10
            )
            r.raise_for_status()
            df = pd.DataFrame(r.json(), columns=[
                'ts', 'open', 'high', 'low', 'close', 'volume',
                'ct', 'qv', 'trades', 'tbv', 'tqv', 'ignore'
            ])
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            return df
        except Exception as e:
            print(f"❌ 獲取K線失敗: {e}")
            return None

    # ══════════════════════════════════════════════
    # LAYER 1: GANN LEVELS (Square of 9)
    # ══════════════════════════════════════════════

    def gann_levels(self, price: float, n: int = 10) -> List[float]:
        """
        Gann Square of 9（大間距版）：每 GANN_STEP 個整數取一個 n²
        step=5 時 BTC $77k 附近層級間距約 $2,700
        例: 255²=65025, 260²=67600, 265²=70225, 270²=72900,
            275²=75625, 280²=78400, 285²=81225, 290²=84100
        """
        base = round(price ** 0.5 / self.gann_step) * self.gann_step
        half = n // 2
        return [float((base + i * self.gann_step) ** 2)
                for i in range(-half, half + 1)
                if (base + i * self.gann_step) > 0]

    def nearest_gann(self, price: float, levels: List[float]) -> Tuple[float, float, float]:
        """返回 (最近Gann線, 下方Gann線, 上方Gann線)"""
        below = [l for l in levels if l <= price]
        above = [l for l in levels if l > price]
        lvl_below = max(below) if below else levels[0]
        lvl_above = min(above) if above else levels[-1]
        nearest = lvl_below if (price - lvl_below) <= (lvl_above - price) else lvl_above
        return nearest, lvl_below, lvl_above

    def near_gann(self, price: float, level: float) -> bool:
        """±0.5% 或 ±$250 取較大值"""
        tol = max(level * self.gann_tol_pct, self.gann_tol_min)
        return abs(price - level) <= tol

    def in_forbidden_zone(self, price: float, lvl_below: float, lvl_above: float) -> bool:
        """兩條 Gann 線正中間禁區（距任何一條都超過容差）"""
        tol_b = max(lvl_below * self.gann_tol_pct, self.gann_tol_min)
        tol_a = max(lvl_above * self.gann_tol_pct, self.gann_tol_min)
        return (price - lvl_below) > tol_b and (lvl_above - price) > tol_a

    # ══════════════════════════════════════════════
    # LAYER 2: TREND (HH/HL vs LH/LL)
    # ══════════════════════════════════════════════

    def detect_swings(self, series: np.ndarray) -> List[float]:
        """簡單擺動高/低點偵測（左右各比較 1 根）"""
        swings = []
        for i in range(1, len(series) - 1):
            if series[i] > series[i-1] and series[i] > series[i+1]:
                swings.append(series[i])
            elif series[i] < series[i-1] and series[i] < series[i+1]:
                swings.append(series[i])
        return swings

    def analyze_trend(self, df: pd.DataFrame) -> str:
        """
        分析最近 trend_lookback 根 15min K線
        要求同時滿足 HH+HL（UP）或 LH+LL（DOWN）才確認趨勢
        返回: 'UP' / 'DOWN' / 'NEUTRAL'
        """
        window = df.tail(self.trend_lookback)
        highs  = window['high'].values
        lows   = window['low'].values
        n = len(highs)

        # 擺動高點
        sh = [highs[i] for i in range(1, n-1) if highs[i] > highs[i-1] and highs[i] > highs[i+1]]
        # 擺動低點
        sl = [lows[i]  for i in range(1, n-1) if lows[i]  < lows[i-1]  and lows[i]  < lows[i+1]]

        if len(sh) >= 2 and len(sl) >= 2:
            hh = sh[-1] > sh[-2]
            hl = sl[-1] > sl[-2]
            lh = sh[-1] < sh[-2]
            ll = sl[-1] < sl[-2]

            # 嚴格：必須同時滿足兩個條件
            if hh and hl:
                return 'UP'
            if lh and ll:
                return 'DOWN'

        return 'NEUTRAL'

    def calc_vwap(self, df: pd.DataFrame) -> float:
        tp = (df['high'] + df['low'] + df['close']) / 3
        return float((tp * df['volume']).sum() / df['volume'].sum())

    # ══════════════════════════════════════════════
    # LAYER 3: CANDLESTICK PATTERNS
    # ══════════════════════════════════════════════

    @staticmethod
    def _body(c) -> float:
        return abs(float(c['close']) - float(c['open']))

    @staticmethod
    def _rng(c) -> float:
        return float(c['high']) - float(c['low'])

    @staticmethod
    def _upper(c) -> float:
        return float(c['high']) - max(float(c['open']), float(c['close']))

    @staticmethod
    def _lower(c) -> float:
        return min(float(c['open']), float(c['close'])) - float(c['low'])

    @staticmethod
    def _bullish(c) -> bool:
        return float(c['close']) > float(c['open'])

    @staticmethod
    def _bearish(c) -> bool:
        return float(c['close']) < float(c['open'])

    def is_hammer(self, c) -> bool:
        """錘頭線：小實體在上，長下影線≥2x實體，上影線≤15%，實體≥最小閾值"""
        b, r = self._body(c), self._rng(c)
        if r == 0 or b < float(c['close']) * 0.001:  # 實體最少0.1%
            return False
        return (b <= r * 0.35 and
                self._lower(c) >= b * 2.0 and
                self._upper(c) <= r * 0.15)

    def is_shooting_star(self, c) -> bool:
        """流星線：小實體在下，長上影線≥2x實體，下影線≤15%，實體≥最小閾值"""
        b, r = self._body(c), self._rng(c)
        if r == 0 or b < float(c['close']) * 0.001:  # 實體最少0.1%
            return False
        return (b <= r * 0.35 and
                self._upper(c) >= b * 2.0 and
                self._lower(c) <= r * 0.15)

    def is_bullish_engulfing(self, prev, curr) -> bool:
        """看漲吞沒：前陰後陽，陽線實體完全包圍陰線"""
        return (self._bearish(prev) and
                self._bullish(curr) and
                float(curr['open'])  <= float(prev['close']) and
                float(curr['close']) >= float(prev['open']))

    def is_bearish_engulfing(self, prev, curr) -> bool:
        """看跌吞沒：前陽後陰，陰線實體完全包圍陽線"""
        return (self._bullish(prev) and
                self._bearish(curr) and
                float(curr['open'])  >= float(prev['close']) and
                float(curr['close']) <= float(prev['open']))

    def is_morning_star(self, c1, c2, c3) -> bool:
        """
        晨星：陰線 + 小實體/十字 + 陽線
        c3 收盤必須高於 c1 中點
        """
        c1_mid = (float(c1['open']) + float(c1['close'])) / 2
        r2 = self._rng(c2)
        small_c2 = (self._body(c2) <= r2 * 0.3) if r2 > 0 else True
        return (self._bearish(c1) and
                small_c2 and
                self._bullish(c3) and
                float(c3['close']) > c1_mid)

    def is_evening_star(self, c1, c2, c3) -> bool:
        """
        黃昏星：陽線 + 小實體/十字 + 陰線
        c3 收盤必須低於 c1 中點
        """
        c1_mid = (float(c1['open']) + float(c1['close'])) / 2
        r2 = self._rng(c2)
        small_c2 = (self._body(c2) <= r2 * 0.3) if r2 > 0 else True
        return (self._bullish(c1) and
                small_c2 and
                self._bearish(c3) and
                float(c3['close']) < c1_mid)

    def detect_pattern(self, df: pd.DataFrame, direction: str) -> Optional[str]:
        """偵測最新 K 線是否符合方向的反轉形態，返回形態名稱或 None"""
        if len(df) < 3:
            return None
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]

        if direction == 'UP':
            if self.is_morning_star(c1, c2, c3):
                return 'MORNING_STAR'
            if self.is_bullish_engulfing(c2, c3):
                return 'BULLISH_ENGULFING'
            if self.is_hammer(c3):
                return 'HAMMER'

        elif direction == 'DOWN':
            if self.is_evening_star(c1, c2, c3):
                return 'EVENING_STAR'
            if self.is_bearish_engulfing(c2, c3):
                return 'BEARISH_ENGULFING'
            if self.is_shooting_star(c3):
                return 'SHOOTING_STAR'

        return None

    # ══════════════════════════════════════════════
    # BOLLINGER BANDS
    # ══════════════════════════════════════════════

    def calc_bb(self, closes: pd.Series) -> Tuple[float, float, float]:
        """返回 (上軌, 中軌, 下軌)"""
        mid = closes.rolling(self.bb_period).mean().iloc[-1]
        std = closes.rolling(self.bb_period).std().iloc[-1]
        return float(mid + self.bb_std * std), float(mid), float(mid - self.bb_std * std)

    # ══════════════════════════════════════════════
    # SL / TP CALCULATION
    # ══════════════════════════════════════════════

    def calc_sl_tp(self, signal_candle, direction: str,
                   tp2_gann: float) -> Tuple[float, float, float]:
        """
        SL：信號K線低點-buffer（LONG） / 高點+buffer（SHORT）
        TP1：1:1 風險回報，平 50% 倉
        TP2：下一條 Gann 線，平剩餘 50%
        """
        entry  = float(signal_candle['close'])
        buffer = entry * 0.001  # 0.1% 緩衝

        if direction == 'UP':
            sl   = float(signal_candle['low']) - buffer
            risk = max(entry - sl, entry * 0.002)
            tp1  = entry + risk
            tp2  = tp2_gann if tp2_gann > entry else entry + risk * 2
        else:
            sl   = float(signal_candle['high']) + buffer
            risk = max(sl - entry, entry * 0.002)
            tp1  = entry - risk
            tp2  = tp2_gann if tp2_gann < entry else entry - risk * 2

        return sl, tp1, tp2

    # ══════════════════════════════════════════════
    # MAIN SIGNAL LOGIC
    # ══════════════════════════════════════════════

    def generate_signal(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        應用三層條件，生成交易信號。
        返回信號 Dict 或 None。
        """
        if len(df) < self.trend_lookback + 5:
            return None

        price = float(df.iloc[-1]['close'])

        # ── 第一層：Gann 磁吸位 ──
        levels             = self.gann_levels(price)
        nearest, lvl_b, lvl_a = self.nearest_gann(price, levels)

        if not self.near_gann(price, nearest):
            return None

        if self.in_forbidden_zone(price, lvl_b, lvl_a):
            return None

        # ── 第二層：趨勢 ──
        trend = self.analyze_trend(df)
        if trend == 'NEUTRAL':
            return None

        vwap = self.calc_vwap(df)

        # ── 第三層：K線形態 ──
        pattern = self.detect_pattern(df, trend)
        if pattern is None:
            return None

        # ── VWAP 方向過濾 ──
        # 上升趨勢：價格須高於 VWAP（支撐有效）
        # 下降趨勢：價格須低於 VWAP（阻力有效）
        if trend == 'UP'   and price < vwap * 0.995:
            return None
        if trend == 'DOWN' and price > vwap * 1.005:
            return None

        # ── BB 加持 ──
        bb_up, bb_mid, bb_dn = self.calc_bb(df['close'])
        bb_boost  = (trend == 'UP'   and price <= bb_dn) or \
                    (trend == 'DOWN' and price >= bb_up)
        strength  = 'ULTRA_STRONG' if bb_boost else 'NORMAL'

        # 洗盤 Bot 模式：只發超強信號
        if self.ultra_only and strength != 'ULTRA_STRONG':
            return None

        # ── SL / TP ──
        tp2_gann  = lvl_a if trend == 'UP' else lvl_b
        sig_candle = df.iloc[-1]
        sl, tp1, tp2 = self.calc_sl_tp(sig_candle, trend, tp2_gann)
        risk = abs(price - sl)

        return {
            'direction':     trend,
            'pattern':       pattern,
            'strength':      strength,
            'entry':         price,
            'sl':            sl,
            'tp1':           tp1,
            'tp2':           tp2,
            'risk':          risk,
            'rr':            abs(tp1 - price) / risk if risk > 0 else 1.0,
            'nearest_gann':  nearest,
            'lvl_below':     lvl_b,
            'lvl_above':     lvl_a,
            'vwap':          vwap,
            'bb_upper':      bb_up,
            'bb_lower':      bb_dn,
            'bb_boost':      bb_boost,
        }

    # ══════════════════════════════════════════════
    # TELEGRAM MESSAGE
    # ══════════════════════════════════════════════

    def format_message(self, sig: Dict) -> str:
        direction = sig['direction']
        pattern   = self.PATTERN_NAMES.get(sig['pattern'], sig['pattern'])
        is_long   = direction == 'UP'

        dir_text  = "📈 LONG" if is_long else "📉 SHORT"
        str_label = "⚡⚡ 超強" if sig['strength'] == 'ULTRA_STRONG' else "✅ 標準"
        bb_line   = "\n⚡ <b>BB突破加持！超強訊號</b>" if sig['bb_boost'] else ""

        vwap_role = "支撐" if is_long else "阻力"
        vwap_diff = sig['entry'] - sig['vwap']
        vwap_note = (f"價格{'高於' if vwap_diff > 0 else '低於'} VWAP "
                     f"${abs(vwap_diff):,.0f} ({'支撐有效' if (is_long and vwap_diff > 0) else 'VWAP作' + vwap_role})")

        sl_pct  = abs(sig['entry'] - sig['sl']) / sig['entry'] * 100
        tp1_pct = abs(sig['tp1']  - sig['entry']) / sig['entry'] * 100

        return f"""
{str_label} <b>ICT + Gann 交易信號</b>  {dir_text}{bb_line}

<b>【交易對】</b>{self.symbol}
<b>【時間】</b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━ 三層條件 ━━━━━
1️⃣ <b>Gann 磁吸位</b>: ${sig['nearest_gann']:,.0f}
   下方: ${sig['lvl_below']:,.0f}  |  上方: ${sig['lvl_above']:,.0f}
2️⃣ <b>趨勢</b>: {'上升趨勢 (HH/HL) ↑' if is_long else '下降趨勢 (LH/LL) ↓'}
3️⃣ <b>K線形態</b>: {pattern}

━━━━━ 進場計劃 ━━━━━
🎯 進場: ${sig['entry']:,.2f}
🛑 止損: ${sig['sl']:,.2f}  (-{sl_pct:.2f}%)
💰 TP1 (平50%): ${sig['tp1']:,.2f}  (+{tp1_pct:.2f}%)
🏆 TP2 (平50%): ${sig['tp2']:,.2f}

━━━━━ 出場規則 ━━━━━
• TP1觸及 → 平50%倉，止損移至入場價 (BE)
• TP2觸及 → 平剩餘50%倉

━━━━━ 輔助指標 ━━━━━
VWAP: ${sig['vwap']:,.2f}  ({vwap_note})
BB上軌: ${sig['bb_upper']:,.0f}  |  BB下軌: ${sig['bb_lower']:,.0f}
"""

    # ══════════════════════════════════════════════
    # COOLDOWN CHECK
    # ══════════════════════════════════════════════

    def should_send(self, sig: Dict) -> bool:
        key = f"{sig['direction']}_{sig['pattern']}"
        if self.last_alert_time is None or key != self.last_alert_key:
            return True
        elapsed = (datetime.now() - self.last_alert_time).total_seconds()
        return elapsed >= self.alert_cooldown

    # ══════════════════════════════════════════════
    # MAIN LOOP
    # ══════════════════════════════════════════════

    async def run(self):
        scan_count = 0
        while True:
            try:
                df = self.fetch_klines('15m', 120)
                if df is None or len(df) < 30:
                    await asyncio.sleep(self.scan_interval)
                    continue

                scan_count += 1
                price  = float(df.iloc[-1]['close'])
                levels = self.gann_levels(price)
                nearest, lvl_b, lvl_a = self.nearest_gann(price, levels)
                near   = self.near_gann(price, nearest)
                trend  = self.analyze_trend(df)
                pattern = self.detect_pattern(df, trend) if trend != 'NEUTRAL' else None

                gann_dist = abs(price - nearest)
                t_icon    = {'UP': '↑', 'DOWN': '↓', 'NEUTRAL': '→'}[trend]
                g_icon    = '🎯' if near else '  '
                p_label   = self.PATTERN_NAMES.get(pattern, '-') if pattern else '-'

                ts = datetime.now().strftime('%H:%M:%S')
                print(f"[{ts}] #{scan_count:04d} ${price:,.2f} | "
                      f"{g_icon} Gann:{nearest:,.0f}(±${gann_dist:,.0f}) | "
                      f"趨勢:{t_icon} | 形態:{p_label}")

                sig = self.generate_signal(df)

                if sig and self.should_send(sig):
                    key = f"{sig['direction']}_{sig['pattern']}"
                    str_label = '⚡超強' if sig['strength'] == 'ULTRA_STRONG' else '標準'
                    print(f"\n{'='*60}")
                    print(f"🔔 信號！{sig['direction']} | {self.PATTERN_NAMES[sig['pattern']]} | {str_label}")
                    print(f"   進場:${sig['entry']:,.2f} | SL:${sig['sl']:,.2f} | TP1:${sig['tp1']:,.2f} | TP2:${sig['tp2']:,.2f}")
                    print(f"{'='*60}\n")

                    msg = self.format_message(sig)

                    if self.telegram.is_configured():
                        await self.telegram.send_alert(msg, None)
                        print("✅ Telegram 已發送")

                    self.last_alert_time = datetime.now()
                    self.last_alert_key  = key

            except KeyboardInterrupt:
                print("\n⏹️  Scanner 已停止")
                break
            except Exception as e:
                print(f"❌ 掃描錯誤: {e}")
                await asyncio.sleep(30)

            await asyncio.sleep(self.scan_interval)


async def main():
    scanner = ICTGannScanner()
    await scanner.run()


if __name__ == '__main__':
    asyncio.run(main())
