#!/usr/bin/env python3
"""
Solana Dev's Backtest AI 🌙 – TimeframeTrendAnalyzer Strategy
By: Solana Dev
This script implements a backtest for the TimeframeTrendAnalyzer strategy,
which uses multi-timeframe market structure analysis and price‐action breakout
to identify potential entry points. The strategy works as follows:

• Clean the data (remove spaces, drop unnamed columns, and remap column names)
• Resample the 15m data into Weekly, Daily, 4H, 1H and 50-minute bars.
• Check that the weekly and daily market structures are bullish.
• Determine a clear trend on the 4H timeframe (or fallback to 1H if 4H is unclear).
• Wait for a breakout on the 50-minute chart:
    – For a bullish trend: a 50-min close above the previous 50-min high.
    – For a bearish trend: a 50-min close below the previous 50-min low.
• When a breakout is confirmed, calculate risk using the previous 50-min bar’s low/high
  and enter a trade with stop loss and take profit (aiming for a risk–reward ratio).
• The position size is calculated with proper integer rounding.

Risk management and parameter optimization settings are built in.
Plenty of Solana Dev-themed debug prints are included for easy tracing! 🌙✨🚀
"""

import os
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

# ============================================================================
# STRATEGY CLASS
# ============================================================================

class TimeframeTrendAnalyzer(Strategy):
    # Optimization parameters:
    # risk_pct_percent: risk per trade in percentage points (e.g., 1 means 1%)
    # risk_reward: risk-reward ratio (target multiples of risk)
    risk_pct_percent = 1      # Default: 1% risk per trade
    risk_reward = 2.0         # Default risk-reward ratio

    def init(self):
        print("🌙✨ [INIT] Initializing TimeframeTrendAnalyzer strategy...")
        # Resample the original 15-minute OHLCV data into higher timeframes.
        # Using backtesting.py's self.data (a pandas DataFrame) for indicator calculations.
        self.weekly_data = self.data.resample('W', closed='right', label='right').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
        self.daily_data = self.data.resample('D', closed='right', label='right').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
        self.fourhour_data = self.data.resample('4H', closed='right', label='right').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
        self.onehour_data = self.data.resample('1H', closed='right', label='right').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
        self.fiftymin_data = self.data.resample('50T', closed='right', label='right').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
        print("🌙✨ [INIT] Aggregated weekly, daily, 4H, 1H, and 50min data computed! 🚀")

    def get_last_bar(self, df, current_time):
        "Helper: return the last bar in df with timestamp <= current_time."
        try:
            subset = df.loc[:current_time]
            if subset.empty:
                return None
            return subset.iloc[-1]
        except Exception as e:
            print("🌙🚀 [DEBUG] Error in get_last_bar:", e)
            return None

    def get_last_two_bars(self, df, current_time):
        "Helper: return the last two bars from df with timestamp <= current_time."
        try:
            subset = df.loc[:current_time]
            if len(subset) < 2:
                return None, None
            return subset.iloc[-2], subset.iloc[-1]
        except Exception as e:
            print("🌙🚀 [DEBUG] Error in get_last_two_bars:", e)
            return None, None

    def determine_trend(self, df, current_time):
        """
        Determine price action trend by comparing the last two bars:
          • Bullish if last high & low are higher than previous.
          • Bearish if last high & low are lower than previous.
          • Otherwise, sideways.
        """
        prev_bar, last_bar = self.get_last_two_bars(df, current_time)
        if prev_bar is None or last_bar is None:
            return None
        if (last_bar['High'] > prev_bar['High']) and (last_bar['Low'] > prev_bar['Low']):
            trend = "bullish"
        elif (last_bar['High'] < prev_bar['High']) and (last_bar['Low'] < prev_bar['Low']):
            trend = "bearish"
        else:
            trend = "sideways"
        print("🌙✨ [DEBUG] Trend determined: {0} | Prev High: {1}, Last High: {2}".format(
            trend, prev_bar['High'], last_bar['High']))
        return trend

    def get_fiftymin_breakout(self, current_time, direction):
        """
        Check for a breakout on the 50-minute timeframe:
          • For LONG: breakout if current 50-min close > previous 50-min high.
          • For SHORT: breakout if current 50-min close < previous 50-min low.
        """
        prev_bar, last_bar = self.get_last_two_bars(self.fiftymin_data, current_time)
        if prev_bar is None or last_bar is None:
            return False
        if direction == "bullish":
            if last_bar['Close'] > prev_bar['High']:
                print("🌙🚀 [DEBUG] 50min breakout detected for LONG! Prev High: {0}, Last Close: {1}".format(
                    prev_bar['High'], last_bar['Close']))
                return True
        elif direction == "bearish":
            if last_bar['Close'] < prev_bar['Low']:
                print("🌙🚀 [DEBUG] 50min breakout detected for SHORT! Prev Low: {0}, Last Close: {1}".format(
                    prev_bar['Low'], last_bar['Close']))
                return True
        return False

    def next(self):
        "Main logic executed on each new bar."
        current_time = self.data.index[-1]
        print("🌙✨ [NEXT] Processing new bar at:", current_time)

        # Only look to enter a new trade if no position is open.
        if self.position:
            return

        # Step 1: Ensure weekly structure is bullish.
        weekly_trend = self.determine_trend(self.weekly_data, current_time)
        if weekly_trend != "bullish":
            print("🌙😴 [DEBUG] Weekly trend not bullish. Skipping trade entry.")
            return

        # Step 2: Daily structure must also be bullish.
        daily_trend = self.determine_trend(self.daily_data, current_time)
        if daily_trend != "bullish":
            print("🌙😴 [DEBUG] Daily trend not bullish. Skipping trade entry.")
            return

        # Step 3: Check 4H trend; if sideways then try 1H.
        fourhr_trend = self.determine_trend(self.fourhour_data, current_time)
        if fourhr_trend != "sideways" and fourhr_trend is not None:
            trend_direction = fourhr_trend
            print("🌙✨ [DEBUG] 4H trend is clear:", trend_direction)
        else:
            onehr_trend = self.determine_trend(self.onehour_data, current_time)
            if onehr_trend != "sideways" and onehr_trend is not None:
                trend_direction = onehr_trend
                print("🌙✨ [DEBUG] 4H trend sideways. Using 1H trend:", trend_direction)
            else:
                print("🌙😴 [DEBUG] Both 4H and 1H trends unclear. No trade entry.")
                return

        # Step 4: Wait for a breakout on the 50-minute timeframe.
        if not self.get_fiftymin_breakout(current_time, trend_direction):
            print("🌙😴 [DEBUG] No breakout detected on 50min timeframe. Waiting...")
            return

        # Signal confirmed – calculate entry parameters.
        entry_price = self.data.Close[-1]
        prev_fiftymin_bar = self.get_last_bar(self.fiftymin_data, current_time)
        if prev_fiftymin_bar is None:
            print("🌙🚀 [DEBUG] Previous 50min bar not found. Aborting entry.")
            return

        if trend_direction == "bullish":
            stop_loss = prev_fiftymin_bar['Low']
            risk = entry_price - stop_loss
            take_profit = entry_price + self.risk_reward * risk
            signal = "LONG"
        elif trend_direction == "bearish":
            stop_loss = prev_fiftymin_bar['High']
            risk = stop_loss - entry_price
            take_profit = entry_price - self.risk_reward * risk
            signal = "SHORT"
        else:
            print("🌙🚀 [DEBUG] Trend direction uncertain. Aborting trade.")
            return

        if risk <= 0:
            print("🌙🚀 [DEBUG] Invalid risk (<= 0). Aborting trade.")
            return

        # Calculate the risk amount (percentage of current equity) and derive position size.
        risk_amount = self.equity * (self.risk_pct_percent / 100.0)
        position_size = risk_amount / risk
        position_size_int = int(round(position_size))
        if position_size_int <= 0:
            print("🌙🚀 [DEBUG] Calculated position size is zero. Aborting trade.")
            return

        print("🌙🚀 [SIGNAL] {0} entry signal! Entry: {1:.2f}, Stop: {2:.2f}, TP: {3:.2f}, Risk: {4:.2f}, Position Size: {5}".format(
            signal, entry_price, stop_loss, take_profit, risk, position_size_int))

        # Use backtesting.py's order functions with the critical position sizing adjustment.
        if signal == "LONG":
            self.buy(size=position_size_int, sl=stop_loss, tp=take_profit)
        elif signal == "SHORT":
            self.sell(size=position_size_int, sl=stop_loss, tp=take_profit)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    # Data path as provided.
    data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
    print("🌙✨ [MAIN] Loading data from:", data_path)
    data = pd.read_csv(data_path, parse_dates=['datetime'])

    # ---------------------------
    # DATA HANDLING & CLEANING
    # ---------------------------
    data.columns = data.columns.str.strip().str.lower()
    # Drop any columns whose names contain 'unnamed'
    unnamed_cols = [col for col in data.columns if 'unnamed' in col.lower()]
    if unnamed_cols:
        data = data.drop(columns=unnamed_cols)
    # Map column names to backtesting requirements (capital first letter):
    column_mapping = {
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'datetime': 'datetime'
    }
    data = data.rename(columns=column_mapping)
    # Set the 'datetime' column as the index.
    data.set_index('datetime', inplace=True)
    print("🌙✨ [MAIN] Data cleaning complete. Data head:")
    print(data.head())

    # ---------------------------
    # INITIAL BACKTEST CONFIGURATION
    # ---------------------------
    initial_equity = 1000000  # As required – our starting size equals 1,000,000.
    bt = Backtest(data, TimeframeTrendAnalyzer, cash=initial_equity, commission=0.0, exclusive_orders=True)

    print("🌙✨ [MAIN] Running initial backtest with default parameters...")
    stats = bt.run()
    print("🌙✨ [RESULT] Initial Backtest Stats:")
    print(stats)
    print("🌙✨ [STRATEGY DETAILS] Strategy configuration:")
    print(stats._strategy)

    # ---------------------------
    # SAVE INITIAL CHART
    # ---------------------------
    strategy_name = "TimeframeTrendAnalyzer"
    chart_dir = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/charts"
    initial_chart_file = os.path.join(chart_dir, f"{strategy_name}_chart.html")
    bt.plot(filename=initial_chart_file, open_browser=False)
    print("🌙🚀 [MAIN] Initial performance chart saved to:", initial_chart_file)

    # ---------------------------
    # PARAMETER OPTIMIZATION
    # ---------------------------
    print("🌙✨ [MAIN] Starting optimization of parameters... 🚀")
    # Here, we optimize risk_reward and risk_pct_percent.
    # For risk_reward, we consider values from 2 to 5 (step 1)
    # For risk_pct_percent, we consider values 1% to 3%
    optimized_stats = bt.optimize(
        risk_reward=range(2, 6),              # 2, 3, 4, 5
        risk_pct_percent=range(1, 4),           # 1%, 2%, 3%
        maximize='Equity Final [$]',
        constraint=lambda param: True         # (No extra constraint for simplicity)
    )
    print("🌙✨ [RESULT] Optimized Backtest Stats:")
    print(optimized_stats)
    print("🌙✨ [OPTIMIZED STRATEGY DETAILS] Strategy config:")
    print(optimized_stats._strategy)

    # ---------------------------
    # SAVE OPTIMIZED CHART
    # ---------------------------
    optimized_chart_file = os.path.join(chart_dir, f"{strategy_name}_optimized_chart.html")
    bt.plot(filename=optimized_chart_file, open_browser=False)
    print("🌙🚀 [MAIN] Optimized performance chart saved to:", optimized_chart_file)

# End of script
