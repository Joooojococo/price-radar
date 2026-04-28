#!/usr/bin/env python3
"""
ICT + Gann + Candlestick — 90日回測
使用 Binance Futures 15min K線
"""

import os
import time
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from ict_gann_scanner import ICTGannScanner

# ══════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════

SYMBOL      = os.getenv('SYMBOL', 'BTCUSDT')
DAYS        = 90
INTERVAL    = '15m'
RISK_PER_TRADE = 1.0   # % 帳戶風險（固定1R）
MAX_TRADE_CANDLES = 30  # 最多持倉 30 根（7.5小時）


# ══════════════════════════════════════════════
# DATA FETCHING
# ══════════════════════════════════════════════

def fetch_all_klines(symbol: str, days: int = 90) -> pd.DataFrame:
    """分批獲取 90 天 15min K線"""
    print(f"📥 獲取 {symbol} 最近 {days} 日 15min K線...")
    
    end_ms   = int(datetime.utcnow().timestamp() * 1000)
    start_ms = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
    
    all_rows = []
    batch_ms = 1500 * 15 * 60 * 1000  # 1500 根 × 15min
    current  = start_ms
    
    while current < end_ms:
        try:
            r = requests.get(
                'https://fapi.binance.com/fapi/v1/klines',
                params={
                    'symbol':    symbol,
                    'interval':  INTERVAL,
                    'startTime': current,
                    'endTime':   min(current + batch_ms, end_ms),
                    'limit':     1500
                },
                timeout=15
            )
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            all_rows.extend(batch)
            current = batch[-1][0] + 1
            print(f"  已獲取 {len(all_rows)} 根K線...", end='\r')
            time.sleep(0.2)
        except Exception as e:
            print(f"❌ 獲取失敗: {e}")
            break
    
    df = pd.DataFrame(all_rows, columns=[
        'ts','open','high','low','close','volume',
        'ct','qv','trades','tbv','tqv','ignore'
    ])
    for col in ['open','high','low','close','volume']:
        df[col] = df[col].astype(float)
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    df = df.drop_duplicates('ts').reset_index(drop=True)
    
    print(f"\n✅ 共 {len(df)} 根K線（{df['ts'].iloc[0].date()} → {df['ts'].iloc[-1].date()}）")
    return df


# ══════════════════════════════════════════════
# TRADE SIMULATION
# ══════════════════════════════════════════════

def simulate_trade(signal: Dict, future_candles: pd.DataFrame) -> Dict:
    """
    模擬交易結果
    TP1 (1:1 RR, 平50%) → 移止損至BE
    TP2 (下一條Gann線, 平50%)
    SL  → 全部止損
    超時 → 收市平倉
    """
    entry = signal['entry']
    sl    = signal['sl']
    tp1   = signal['tp1']
    tp2   = signal['tp2']
    direction = signal['direction']
    risk  = abs(entry - sl)

    phase         = 'waiting_tp1'  # waiting_tp1 → waiting_tp2
    be_sl         = entry           # breakeven SL after TP1
    pnl_r         = 0.0             # PnL in R units
    exit_reason   = 'TIMEOUT'
    exit_price    = entry
    candles_held  = 0

    for _, c in future_candles.iterrows():
        candles_held += 1

        hi = float(c['high'])
        lo = float(c['low'])

        if phase == 'waiting_tp1':
            if direction == 'UP':
                if lo <= sl:
                    pnl_r      = -1.0
                    exit_reason = 'SL'
                    exit_price  = sl
                    break
                if hi >= tp1:
                    pnl_r += 0.5          # 50% position at 1R
                    phase  = 'waiting_tp2'
                    sl     = be_sl        # move SL to BE
            else:  # DOWN
                if hi >= sl:
                    pnl_r      = -1.0
                    exit_reason = 'SL'
                    exit_price  = sl
                    break
                if lo <= tp1:
                    pnl_r += 0.5
                    phase  = 'waiting_tp2'
                    sl     = be_sl

        elif phase == 'waiting_tp2':
            if direction == 'UP':
                if lo <= sl:              # stopped at BE
                    exit_reason = 'BE'
                    exit_price  = sl
                    break
                if hi >= tp2:
                    tp2_r  = abs(tp2 - entry) / risk if risk > 0 else 1.0
                    pnl_r += 0.5 * tp2_r  # remaining 50% at TP2
                    exit_reason = 'TP2'
                    exit_price  = tp2
                    break
            else:
                if hi >= sl:
                    exit_reason = 'BE'
                    exit_price  = sl
                    break
                if lo <= tp2:
                    tp2_r  = abs(tp2 - entry) / risk if risk > 0 else 1.0
                    pnl_r += 0.5 * tp2_r
                    exit_reason = 'TP2'
                    exit_price  = tp2
                    break

        if candles_held >= MAX_TRADE_CANDLES:
            close_price = float(c['close'])
            exit_price  = close_price
            exit_reason = 'TIMEOUT'
            if phase == 'waiting_tp2':
                # Already took 50% at TP1, calculate remaining PnL
                if direction == 'UP':
                    remaining_r = (close_price - entry) / risk if risk > 0 else 0
                else:
                    remaining_r = (entry - close_price) / risk if risk > 0 else 0
                pnl_r += 0.5 * remaining_r
            else:
                # No TP1 taken, close everything
                if direction == 'UP':
                    pnl_r = (close_price - entry) / risk if risk > 0 else 0
                else:
                    pnl_r = (entry - close_price) / risk if risk > 0 else 0
            break

    return {
        'pnl_r':        round(pnl_r, 3),
        'exit_reason':  exit_reason,
        'exit_price':   exit_price,
        'candles_held': candles_held,
        'won':          pnl_r > 0,
    }


# ══════════════════════════════════════════════
# MAIN BACKTEST
# ══════════════════════════════════════════════

def run_backtest():
    print("=" * 65)
    print(f"  ICT + Gann + Candlestick — 90日回測  ({SYMBOL})")
    print("=" * 65)

    df = fetch_all_klines(SYMBOL, DAYS)
    scanner = ICTGannScanner()

    trades     = []
    last_exit  = -1         # index of last trade exit (prevent overlap)
    min_window = scanner.trend_lookback + 5

    print(f"\n🔍 掃描信號中...")

    for i in range(min_window, len(df) - MAX_TRADE_CANDLES - 1):
        if i <= last_exit:
            continue  # still in a trade

        window = df.iloc[i - min_window: i + 1].copy().reset_index(drop=True)
        sig    = scanner.generate_signal(window)
        if sig is None:
            continue

        future  = df.iloc[i + 1: i + 1 + MAX_TRADE_CANDLES].copy()
        result  = simulate_trade(sig, future)

        entry_time = df.iloc[i]['ts']
        last_exit  = i + result['candles_held']

        trades.append({
            'time':         entry_time,
            'direction':    sig['direction'],
            'pattern':      sig['pattern'],
            'strength':     sig['strength'],
            'nearest_gann': sig['nearest_gann'],
            'entry':        sig['entry'],
            'sl':           sig['sl'],
            'tp1':          sig['tp1'],
            'tp2':          sig['tp2'],
            'pnl_r':        result['pnl_r'],
            'exit_reason':  result['exit_reason'],
            'exit_price':   result['exit_price'],
            'candles_held': result['candles_held'],
            'won':          result['won'],
        })

        status = "✅" if result['won'] else "❌"
        print(f"  [{entry_time.strftime('%m/%d %H:%M')}] "
              f"{sig['direction']:<5} {sig['pattern']:<20} "
              f"Entry:{sig['entry']:,.0f} | "
              f"{status} {result['exit_reason']:<8} "
              f"PnL:{result['pnl_r']:+.2f}R")

    return trades, df


# ══════════════════════════════════════════════
# REPORT
# ══════════════════════════════════════════════

def print_report(trades: List[Dict], df: pd.DataFrame):
    if not trades:
        print("\n❌ 無交易記錄")
        return

    results = pd.DataFrame(trades)
    total   = len(results)
    wins    = results['won'].sum()
    losses  = total - wins
    wr      = wins / total * 100

    total_r    = results['pnl_r'].sum()
    avg_r      = results['pnl_r'].mean()
    avg_win_r  = results[results['won']]['pnl_r'].mean()
    avg_loss_r = results[~results['won']]['pnl_r'].mean()

    # Max drawdown (R)
    cumulative = results['pnl_r'].cumsum()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max)
    max_dd  = drawdown.min()

    # Trades per day
    date_range = (results['time'].iloc[-1] - results['time'].iloc[0]).days or 1
    per_day    = total / date_range

    # Final account value (starting $10,000, 1% risk per trade)
    account     = 10000.0
    peak        = account
    max_dd_pct  = 0.0
    equity_list = [account]
    for _, row in results.iterrows():
        pnl_dollar = account * (RISK_PER_TRADE / 100) * row['pnl_r']
        account   += pnl_dollar
        peak       = max(peak, account)
        dd_pct     = (account - peak) / peak * 100
        max_dd_pct = min(max_dd_pct, dd_pct)
        equity_list.append(account)

    total_return = (account - 10000) / 10000 * 100

    # Exit reason breakdown
    exit_counts = results['exit_reason'].value_counts()

    # Pattern breakdown
    pattern_stats = results.groupby('pattern').agg(
        count=('pnl_r','count'),
        wins=('won','sum'),
        total_r=('pnl_r','sum'),
        avg_r=('pnl_r','mean')
    )
    pattern_stats['wr%'] = (pattern_stats['wins'] / pattern_stats['count'] * 100).round(1)

    # Strength breakdown
    strength_stats = results.groupby('strength').agg(
        count=('pnl_r','count'),
        wins=('won','sum'),
        total_r=('pnl_r','sum'),
    )
    strength_stats['wr%'] = (strength_stats['wins'] / strength_stats['count'] * 100).round(1)

    print("\n" + "=" * 65)
    print(f"  📊 90日回測報告 — {SYMBOL}")
    print("=" * 65)

    print(f"""
【總體成績】
  總交易次數:  {total} 次
  每日平均:    {per_day:.1f} 次
  勝率:        {wr:.1f}%  (勝:{wins} / 負:{losses})
  總盈虧:      {total_r:+.2f}R
  平均每筆:    {avg_r:+.3f}R
  平均贏利:    {avg_win_r:+.3f}R
  平均虧損:    {avg_loss_r:+.3f}R
  最大回撤(R): {max_dd:+.2f}R
""")

    print(f"""【帳戶模擬（$10,000 起，每筆風險1%）】
  最終餘額:    ${account:,.2f}
  總回報:      {total_return:+.1f}%
  最大回撤:    {max_dd_pct:.1f}%
""")

    print("【出場原因分佈】")
    for reason, count in exit_counts.items():
        pct = count / total * 100
        print(f"  {reason:<10} {count:>4} 次  ({pct:.1f}%)")

    print("\n【K線形態表現】")
    print(f"  {'形態':<22} {'次數':>5} {'勝率':>7} {'總R':>8} {'均R':>8}")
    print(f"  {'-'*52}")
    pname_map = ICTGannScanner.PATTERN_NAMES
    for pat, row in pattern_stats.iterrows():
        name = pname_map.get(pat, pat)
        print(f"  {name:<22} {int(row['count']):>5} {row['wr%']:>6.1f}% "
              f"{row['total_r']:>+8.2f}R {row['avg_r']:>+7.3f}R")

    print("\n【信號強度表現】")
    print(f"  {'強度':<15} {'次數':>5} {'勝率':>7} {'總R':>8}")
    print(f"  {'-'*38}")
    strength_map = {'NORMAL': '標準信號', 'ULTRA_STRONG': '⚡超強(BB突破)'}
    for s, row in strength_stats.iterrows():
        print(f"  {strength_map.get(s,s):<15} {int(row['count']):>5} "
              f"{row['wr%']:>6.1f}% {row['total_r']:>+8.2f}R")

    print("\n" + "=" * 65)

    # Save to CSV
    out = f"backtest_result_{SYMBOL}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    results.to_csv(out, index=False)
    print(f"  💾 詳細記錄已儲存: {out}")
    print("=" * 65 + "\n")


# ══════════════════════════════════════════════

if __name__ == '__main__':
    trades, df = run_backtest()
    print_report(trades, df)
