#!/usr/bin/env python3
"""
Gann Horizontal Line Strategy Backtest
Backtest for BTC 1-minute timeframe over past 1 month
"""

import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from pybit.unified_trading import HTTP
from dotenv import load_dotenv

load_dotenv()


class GannHorizontalLines:
    """Gann Horizontal Line Calculator"""
    
    def __init__(self, price_range: Tuple[float, float]):
        """
        Initialize Gann lines for a price range
        
        Args:
            price_range: (min_price, max_price) to generate lines for
        """
        self.lines = self._calculate_gann_lines(price_range)
    
    def _calculate_gann_lines(self, price_range: Tuple[float, float]) -> List[float]:
        """
        Calculate Gann horizontal lines based on square numbers
        
        Rule: 
        - If n^2 is odd, use n^2
        - If n^2 is even, use n^2 + 1
        """
        min_price, max_price = price_range
        lines = []
        
        # Find appropriate n range
        # For BTC prices around 90,000-100,000, we need n around 300-316
        n = 1
        while True:
            square = n * n
            gann_line = square if square % 2 == 1 else square + 1
            
            if gann_line > max_price * 1.1:  # Add 10% buffer
                break
            
            if gann_line >= min_price * 0.9:  # Add 10% buffer
                lines.append(gann_line)
            
            n += 1
        
        return sorted(lines)
    
    def get_nearest_line(self, price: float, direction: str = 'both') -> Optional[float]:
        """
        Get the nearest Gann line to a price
        
        Args:
            price: Current price
            direction: 'above', 'below', or 'both'
        """
        if not self.lines:
            return None
        
        if direction == 'above':
            above_lines = [line for line in self.lines if line > price]
            return min(above_lines) if above_lines else None
        elif direction == 'below':
            below_lines = [line for line in self.lines if line < price]
            return max(below_lines) if below_lines else None
        else:
            distances = [(abs(line - price), line) for line in self.lines]
            return min(distances, key=lambda x: x[0])[1]
    
    def is_near_line(self, price: float, threshold: float = 0.002) -> Tuple[bool, Optional[float]]:
        """
        Check if price is near a Gann line
        
        Args:
            price: Current price
            threshold: Percentage threshold (default 0.2%)
            
        Returns:
            (is_near, line_value)
        """
        nearest = self.get_nearest_line(price)
        if nearest is None:
            return False, None
        
        distance_pct = abs(price - nearest) / nearest
        return distance_pct <= threshold, nearest
    
    def get_next_line(self, current_line: float, direction: str) -> Optional[float]:
        """
        Get the next Gann line in a direction
        
        Args:
            current_line: Current line value
            direction: 'up' or 'down'
        """
        try:
            idx = self.lines.index(current_line)
            if direction == 'up' and idx < len(self.lines) - 1:
                return self.lines[idx + 1]
            elif direction == 'down' and idx > 0:
                return self.lines[idx - 1]
        except ValueError:
            pass
        return None


class CandlestickPatterns:
    """Candlestick Pattern Detection"""
    
    @staticmethod
    def is_hammer(df: pd.DataFrame, idx: int) -> bool:
        """
        Detect Hammer pattern (long lower shadow, small body at top)
        
        Args:
            df: DataFrame with OHLC data
            idx: Index of candle to check
        """
        if idx < 0 or idx >= len(df):
            return False
        
        row = df.iloc[idx]
        open_price = row['open']
        high = row['high']
        low = row['low']
        close = row['close']
        
        # Calculate body and shadows
        body = abs(close - open_price)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        total_range = high - low
        
        if total_range == 0:
            return False
        
        # Hammer criteria:
        # 1. Lower shadow at least 2x body
        # 2. Upper shadow small (less than 10% of total range)
        # 3. Body in upper part of candle
        lower_shadow_ratio = lower_shadow / body if body > 0 else 0
        upper_shadow_ratio = upper_shadow / total_range
        body_position = (min(open_price, close) - low) / total_range
        
        return (lower_shadow_ratio >= 2.0 and 
                upper_shadow_ratio <= 0.1 and 
                body_position >= 0.7)
    
    @staticmethod
    def is_bullish_engulfing(df: pd.DataFrame, idx: int) -> bool:
        """
        Detect Bullish Engulfing pattern
        
        Args:
            df: DataFrame with OHLC data
            idx: Index of the engulfing candle (second candle)
        """
        if idx < 1 or idx >= len(df):
            return False
        
        prev_row = df.iloc[idx - 1]
        curr_row = df.iloc[idx]
        
        prev_open = prev_row['open']
        prev_close = prev_row['close']
        curr_open = curr_row['open']
        curr_close = curr_row['close']
        
        # Previous candle should be bearish (close < open)
        is_prev_bearish = prev_close < prev_open
        
        # Current candle should be bullish (close > open)
        is_curr_bullish = curr_close > curr_open
        
        # Current candle should engulf previous
        # Current open below previous close
        # Current close above previous open
        engulfs = (curr_open < prev_close) and (curr_close > prev_open)
        
        return is_prev_bearish and is_curr_bullish and engulfs
    
    @staticmethod
    def is_bearish_engulfing(df: pd.DataFrame, idx: int) -> bool:
        """
        Detect Bearish Engulfing pattern
        
        Args:
            df: DataFrame with OHLC data
            idx: Index of the engulfing candle (second candle)
        """
        if idx < 1 or idx >= len(df):
            return False
        
        prev_row = df.iloc[idx - 1]
        curr_row = df.iloc[idx]
        
        prev_open = prev_row['open']
        prev_close = prev_row['close']
        curr_open = curr_row['open']
        curr_close = curr_row['close']
        
        # Previous candle should be bullish (close > open)
        is_prev_bullish = prev_close > prev_open
        
        # Current candle should be bearish (close < open)
        is_curr_bearish = curr_close < curr_open
        
        # Current candle should engulf previous
        # Current open above previous close
        # Current close below previous open
        engulfs = (curr_open > prev_close) and (curr_close < prev_open)
        
        return is_prev_bullish and is_curr_bearish and engulfs
    
    @staticmethod
    def is_evening_star(df: pd.DataFrame, idx: int) -> bool:
        """
        Detect Evening Star pattern (3-candle reversal at top)
        
        Args:
            df: DataFrame with OHLC data
            idx: Index of the third candle (confirmation)
        """
        if idx < 2 or idx >= len(df):
            return False
        
        first = df.iloc[idx - 2]
        second = df.iloc[idx - 1]
        third = df.iloc[idx]
        
        # First candle: bullish
        is_first_bullish = first['close'] > first['open']
        
        # Second candle: small body (doji or spinning top)
        second_body = abs(second['close'] - second['open'])
        second_range = second['high'] - second['low']
        is_small_body = second_body / second_range < 0.3 if second_range > 0 else False
        
        # Second candle gaps up (trades above first candle's body)
        gaps_up = second['low'] > first['close']
        
        # Third candle: bearish and closes below midpoint of first candle
        is_third_bearish = third['close'] < third['open']
        first_midpoint = (first['open'] + first['close']) / 2
        closes_below_mid = third['close'] < first_midpoint
        
        return is_first_bullish and is_small_body and gaps_up and is_third_bearish and closes_below_mid


class GannBacktester:
    """Backtest Engine for Gann Strategy"""
    
    def __init__(self, symbol: str = 'BTCUSDT'):
        """Initialize backtester"""
        self.symbol = symbol
        self.session = HTTP(
            testnet=os.getenv('BYBIT_TESTNET', 'false').lower() == 'true',
            api_key=os.getenv('BYBIT_API_KEY'),
            api_secret=os.getenv('BYBIT_API_SECRET')
        )
        
        # Strategy parameters
        self.sl_buffer = 10  # $10 buffer for stop loss
        self.proximity_threshold = 0.002  # 0.2% proximity to Gann line
        self.risk_per_trade = 0.01  # 1% risk per trade
        
        # Trade tracking
        self.trades = []
        self.equity_curve = []
    
    def fetch_historical_data(self, interval: str = '1', days: int = 30) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from Bybit
        
        Args:
            interval: Bybit interval format ('1' for 1-minute)
            days: Number of days to fetch
        """
        print(f"Fetching {days} days of {self.symbol} {interval}-minute data...")
        
        # Bybit API limit is 1000 candles per request
        # 30 days * 24 hours * 60 minutes = 43,200 candles
        # Need multiple requests
        all_data = []
        end_time = int(datetime.now().timestamp() * 1000)
        
        while len(all_data) < days * 24 * 60:
            limit = min(1000, days * 24 * 60 - len(all_data))
            
            try:
                response = self.session.get_kline(
                    category="linear",
                    symbol=self.symbol,
                    interval=interval,
                    limit=limit,
                    end=end_time
                )
                
                if response['retCode'] == 0:
                    klines = response['result']['list']
                    all_data.extend(klines)
                    end_time = int(klines[-1][0]) - 1  # Move to next batch
                    print(f"Fetched {len(klines)} candles, total: {len(all_data)}")
                else:
                    print(f"API Error: {response['retMsg']}")
                    break
                    
            except Exception as e:
                print(f"Error fetching data: {e}")
                break
            
            time.sleep(0.1)  # Rate limiting
        
        if not all_data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
        ])
        
        # Convert data types
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        # Sort by timestamp ascending
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        print(f"Total candles fetched: {len(df)}")
        return df
    
    def run_backtest(self, df: pd.DataFrame, initial_capital: float = 10000):
        """
        Run the backtest
        
        Args:
            df: Historical OHLCV data
            initial_capital: Starting capital
        """
        print("\n" + "="*60)
        print("Starting Gann Strategy Backtest")
        print("="*60)
        
        # Initialize Gann lines based on price range
        min_price = df['low'].min()
        max_price = df['high'].max()
        gann = GannHorizontalLines((min_price, max_price))
        
        print(f"\nGann Lines ({len(gann.lines)} lines):")
        print(gann.lines[:10], "...", gann.lines[-10:])
        
        # Initialize tracking
        capital = initial_capital
        position = None  # None, 'long', or 'short'
        entry_price = 0
        entry_time = None
        stop_loss = 0
        take_profit_1 = 0
        tp1_hit = False
        entry_line = 0
        
        patterns = CandlestickPatterns()
        
        # Iterate through candles
        for i in range(2, len(df)):
            current_candle = df.iloc[i]
            current_price = current_candle['close']
            current_time = current_candle['timestamp']
            
            # Check if we have an open position
            if position is not None:
                # Check stop loss
                if position == 'long' and current_candle['low'] <= stop_loss:
                    # Stop loss hit
                    pnl = (stop_loss - entry_price) / entry_price
                    capital *= (1 + pnl * self.risk_per_trade * 10)  # Adjust for leverage
                    self._record_trade('SL', entry_price, stop_loss, pnl, current_time, capital)
                    position = None
                
                elif position == 'short' and current_candle['high'] >= stop_loss:
                    # Stop loss hit
                    pnl = (entry_price - stop_loss) / entry_price
                    capital *= (1 + pnl * self.risk_per_trade * 10)
                    self._record_trade('SL', entry_price, stop_loss, pnl, current_time, capital)
                    position = None
                
                # Check TP1 (1:1 risk:reward)
                elif not tp1_hit:
                    if position == 'long' and current_candle['high'] >= take_profit_1:
                        # TP1 hit - close 50%, move SL to breakeven
                        pnl_1 = (take_profit_1 - entry_price) / entry_price
                        capital *= (1 + pnl_1 * self.risk_per_trade * 5)  # 50% position
                        tp1_hit = True
                        stop_loss = entry_price  # Move to breakeven
                        self._record_trade('TP1', entry_price, take_profit_1, pnl_1, current_time, capital)
                    
                    elif position == 'short' and current_candle['low'] <= take_profit_1:
                        # TP1 hit - close 50%, move SL to breakeven
                        pnl_1 = (entry_price - take_profit_1) / entry_price
                        capital *= (1 + pnl_1 * self.risk_per_trade * 5)
                        tp1_hit = True
                        stop_loss = entry_price
                        self._record_trade('TP1', entry_price, take_profit_1, pnl_1, current_time, capital)
                
                # Check TP2 (next Gann line)
                else:
                    next_line = gann.get_next_line(entry_line, 'up' if position == 'long' else 'down')
                    if next_line:
                        if position == 'long' and current_candle['high'] >= next_line:
                            # TP2 hit
                            pnl_2 = (next_line - entry_price) / entry_price
                            capital *= (1 + pnl_2 * self.risk_per_trade * 5)
                            self._record_trade('TP2', entry_price, next_line, pnl_2, current_time, capital)
                            position = None
                        
                        elif position == 'short' and current_candle['low'] <= next_line:
                            # TP2 hit
                            pnl_2 = (entry_price - next_line) / entry_price
                            capital *= (1 + pnl_2 * self.risk_per_trade * 5)
                            self._record_trade('TP2', entry_price, next_line, pnl_2, current_time, capital)
                            position = None
            
            # If no position, look for entry signals
            else:
                # Check if price is near a Gann line
                is_near, gann_line = gann.is_near_line(current_price, self.proximity_threshold)
                
                if is_near and gann_line:
                    # Determine if we're above or below the line
                    is_above = current_price > gann_line
                    
                    # Check for long signals (price above line, retesting from above)
                    if is_above:
                        # Look for hammer or bullish engulfing
                        if patterns.is_hammer(df, i) or patterns.is_bullish_engulfing(df, i):
                            # Enter long on next candle
                            if i + 1 < len(df):
                                entry_price = df.iloc[i + 1]['open']
                                entry_time = df.iloc[i + 1]['timestamp']
                                stop_loss = df.iloc[i]['low'] - self.sl_buffer
                                take_profit_1 = entry_price + (entry_price - stop_loss)
                                entry_line = gann_line
                                position = 'long'
                                tp1_hit = False
                                print(f"\nLONG entry at ${entry_price:,.2f} | Gann Line: ${gann_line:,.0f}")
                    
                    # Check for short signals (price below line, retesting from below)
                    else:
                        # Look for bearish engulfing or evening star
                        if patterns.is_bearish_engulfing(df, i) or patterns.is_evening_star(df, i):
                            # Enter short on next candle
                            if i + 1 < len(df):
                                entry_price = df.iloc[i + 1]['open']
                                entry_time = df.iloc[i + 1]['timestamp']
                                stop_loss = df.iloc[i]['high'] + self.sl_buffer
                                take_profit_1 = entry_price - (stop_loss - entry_price)
                                entry_line = gann_line
                                position = 'short'
                                tp1_hit = False
                                print(f"\nSHORT entry at ${entry_price:,.2f} | Gann Line: ${gann_line:,.0f}")
            
            # Record equity
            self.equity_curve.append({
                'timestamp': current_time,
                'capital': capital
            })
        
        # Close any remaining position at end
        if position is not None:
            final_price = df.iloc[-1]['close']
            if position == 'long':
                pnl = (final_price - entry_price) / entry_price
            else:
                pnl = (entry_price - final_price) / entry_price
            capital *= (1 + pnl * self.risk_per_trade * 10)
            self._record_trade('FORCE_CLOSE', entry_price, final_price, pnl, df.iloc[-1]['timestamp'], capital)
        
        print("\n" + "="*60)
        print("Backtest Complete")
        print("="*60)
    
    def _record_trade(self, exit_type: str, entry_price: float, exit_price: float, 
                      pnl: float, exit_time: datetime, capital: float):
        """Record a trade"""
        self.trades.append({
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'exit_type': exit_type,
            'exit_time': exit_time,
            'capital': capital
        })
    
    def generate_report(self):
        """Generate backtest report"""
        if not self.trades:
            print("No trades recorded")
            return
        
        df_trades = pd.DataFrame(self.trades)
        
        # Calculate statistics
        total_trades = len(df_trades)
        winning_trades = len(df_trades[df_trades['pnl'] > 0])
        losing_trades = len(df_trades[df_trades['pnl'] < 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        avg_win = df_trades[df_trades['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = df_trades[df_trades['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        total_return = (df_trades['capital'].iloc[-1] / df_trades['capital'].iloc[0] - 1) * 100
        max_drawdown = self._calculate_max_drawdown()
        
        # Exit type breakdown
        exit_counts = df_trades['exit_type'].value_counts()
        
        print("\n" + "="*60)
        print("BACKTEST REPORT")
        print("="*60)
        print(f"\n📊 Trade Statistics:")
        print(f"   Total Trades: {total_trades}")
        print(f"   Winning Trades: {winning_trades}")
        print(f"   Losing Trades: {losing_trades}")
        print(f"   Win Rate: {win_rate:.2%}")
        print(f"   Average Win: {avg_win:.2%}")
        print(f"   Average Loss: {avg_loss:.2%}")
        print(f"   Profit Factor: {abs(avg_win * winning_trades / (avg_loss * losing_trades)):.2f}" if losing_trades > 0 else "   Profit Factor: N/A")
        
        print(f"\n💰 Performance:")
        print(f"   Total Return: {total_return:.2f}%")
        print(f"   Max Drawdown: {max_drawdown:.2f}%")
        
        print(f"\n🎯 Exit Breakdown:")
        for exit_type, count in exit_counts.items():
            print(f"   {exit_type}: {count} ({count/total_trades:.1%})")
        
        print("\n" + "="*60)
        
        # Save detailed trades to CSV
        output_file = f"gann_backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df_trades.to_csv(output_file, index=False)
        print(f"\n📁 Detailed trades saved to: {output_file}")
        
        # Save equity curve
        df_equity = pd.DataFrame(self.equity_curve)
        equity_file = f"gann_equity_curve_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df_equity.to_csv(equity_file, index=False)
        print(f"📁 Equity curve saved to: {equity_file}")
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if not self.equity_curve:
            return 0
        
        df_equity = pd.DataFrame(self.equity_curve)
        peak = df_equity['capital'].expanding().max()
        drawdown = (df_equity['capital'] - peak) / peak
        return drawdown.min() * 100


def main():
    """Main function"""
    print("="*60)
    print("Gann Horizontal Line Strategy Backtest")
    print("="*60)
    
    # Initialize backtester
    backtester = GannBacktester(symbol='BTCUSDT')
    
    # Fetch data (1-minute, 30 days)
    df = backtester.fetch_historical_data(interval='1', days=30)
    
    if df.empty:
        print("Failed to fetch data")
        return
    
    print(f"\nData range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Price range: ${df['low'].min():,.2f} to ${df['high'].max():,.2f}")
    
    # Run backtest
    backtester.run_backtest(df, initial_capital=10000)
    
    # Generate report
    backtester.generate_report()


if __name__ == "__main__":
    main()
