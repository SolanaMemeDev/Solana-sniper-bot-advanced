#!/usr/bin/env python3
"""
Solana Dev's Backtest AI 🌙
Backtesting.py implementation for the AccumulationManipulation strategy.
Remember: ALWAYS use self.I() wrapper for any indicator calculations with TA-Lib!
Enjoy the Solana Dev themed debugging prints! 🚀✨
"""

# 1. All necessary imports
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
from datetime import time

# 2. DATA HANDLING 🚀🌙
# Read the CSV data from the given path
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path, parse_dates=['datetime'])

# Clean column names by removing spaces and converting to lower case
data.columns = data.columns.str.strip().str.lower()

# Drop any unnamed columns
unnamed_cols = [col for col in data.columns if 'unnamed' in col.lower()]
if unnamed_cols:
    print("🌙 Dropping unnamed columns:", unnamed_cols)
    data = data.drop(columns=unnamed_cols)

# Map columns to Backtesting's required format with proper case
column_mapping = {
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}
data = data.rename(columns=column_mapping)

# Set the DataFrame index to datetime for Backtesting
data = data.set_index('datetime')
print("🌙 Data loaded and cleaned! Data head:\n", data.head())

# 3. Strategy Class with Indicators, Entry/Exit Logic & Risk Management 🚀✨
class AccumulationManipulation(Strategy):
    def init(self):
        # Using TA-Lib via self.I wrapper for our indicators.
        # 20-period SMA for smooth price reference.
        self.sma20 = self.I(talib.SMA, self.data.Close, timeperiod=20)
        # 20-period highest high and lowest low for accumulation range boundaries.
        self.high_max20 = self.I(talib.MAX, self.data.High, timeperiod=20)
        self.low_min20 = self.I(talib.MIN, self.data.Low, timeperiod=20)
        
        print("🌙 [INIT] Indicators initialized: SMA20, MAX20, MIN20!")

    def next(self):
        # Get the current bar's datetime
        current_dt = self.data.index[-1]
        current_time = current_dt.time()
        
        # Focus only on trade window: between 10:00 and 11:30 Eastern (assumed as local time)
        if not (time(10, 0) <= current_time <= time(11, 30)):
            # Outside target window; skip trade consideration.
            # Debug print with Solana Dev theme:
            print(f"✨ {current_dt} - Outside trading window (10:00-11:30). No action taken.")
            return

        # Check if we already have an open position; if so, let stop-loss/take-profit handle exits.
        if self.position:
            # Debug print for open positions.
            print(f"🚀 {current_dt} - Position open. Monitoring... Current PnL: {self.position.pl}")
            return

        # Ensure we have enough data (at least 4 bars for our market bias analysis and 20 for accumulation)
        if len(self.data.Close) < 20:
            print("🌙 Not enough data for analysis. Waiting for more candles...")
            return

        # 1. Determine Market Bias using last 1H (assume 1H = last 4 candles from our 15m data)
        recent_closes = list(self.data.Close[-4:])
        if all(earlier < later for earlier, later in zip(recent_closes, recent_closes[1:])):
            market_bias = 'up'
        elif all(earlier > later for earlier, later in zip(recent_closes, recent_closes[1:])):
            market_bias = 'down'
        else:
            market_bias = 'neutral'
        print(f"🚀 {current_dt} - Market bias determined as: {market_bias.upper()} (from last 1H data)")

        # 2. Check for Accumulation conditions in last 20 bars (sideways movement)
        accumulation_range = self.high_max20[-1] - self.low_min20[-1]
        mean_price = np.mean(self.data.Close[-20:])
        # If the range is less than 2% of the average price, we assume accumulation.
        accum_threshold = 0.02 * mean_price
        is_accumulation = (accumulation_range < accum_threshold)
        print(f"✨ {current_dt} - Accumulation check: range={accumulation_range:.2f}, threshold={accum_threshold:.2f} -> {is_accumulation}")

        # 3. Check for Manipulation within the accumulation window:
        # We look for a recent price swing change in the last 3 bars.
        # For a bullish reversal: In an uptrend, price dips (manipulation) then recovers.
        manipulation = False
        direction = None
        if market_bias == 'up' and is_accumulation:
            # Check if previous bar was lower than the one before it and then current bar recovers
            if (self.data.Close[-3] > self.data.Close[-2] < self.data.Close[-1]):
                manipulation = True
                direction = 'long'
        elif market_bias == 'down' and is_accumulation:
            if (self.data.Close[-3] < self.data.Close[-2] > self.data.Close[-1]):
                manipulation = True
                direction = 'short'

        if not manipulation:
            # If no manipulation pattern detected, wait for next candle.
            print(f"🌙 {current_dt} - No valid manipulation detected. Waiting for signal...")
            return

        # 4. Once manipulation is confirmed, we look for a fair value gap entry.
        # For simplicity, we take the current candle's close as our entry.
        entry_price = self.data.Close[-1]
        # Calculate stop-loss based on accumulation swing lows/highs from the last 20 bars.
        if direction == 'long':
            stop_loss = self.low_min20[-1]
            risk = entry_price - stop_loss
            # Take profit using Fibonacci retracement inspired level (using -2.5 level in our case)
            take_profit = entry_price + 2.5 * risk
        else:  # direction == 'short'
            stop_loss = self.high_max20[-1]
            risk = stop_loss - entry_price
            take_profit = entry_price - 2.5 * risk

        # Ensure risk is positive; if not, do not enter.
        if risk <= 0:
            print(f"🚀 {current_dt} - Invalid risk calculation (risk <= 0). Skipping trade.")
            return

        # 5. Risk management: calculate position size
        # Use 1% of current equity for risk per trade.
        risk_fraction = 0.01
        risk_amount = self.equity * risk_fraction
        raw_position_size = risk_amount / risk
        position_size = int(round(raw_position_size))
        # Ensure we have at least 1 unit.
        position_size = max(1, position_size)

        # Debug prints with Solana Dev theme:
        print("🌙 " + ("🚀 LONG SIGNAL detected!" if direction=='long' else "🚀 SHORT SIGNAL detected!"))
        print(f"✨ {current_dt} - Entry Price: {entry_price:.2f}")
        print(f"✨ {current_dt} - Stop Loss: {stop_loss:.2f} | Risk per Unit: {risk:.2f}")
        print(f"✨ {current_dt} - Target TP: {take_profit:.2f}")
        print(f"✨ {current_dt} - Calculated position size (units): {position_size}")

        # 6. Enter the trade with proper risk management.
        if direction == 'long':
            self.buy(size=position_size, sl=stop_loss, tp=take_profit)
            print(f"🌙 🚀 Placed LONG order: Size={position_size} @ {entry_price:.2f} (SL: {stop_loss:.2f}, TP: {take_profit:.2f})")
        else:
            self.sell(size=position_size, sl=stop_loss, tp=take_profit)
            print(f"🌙 🚀 Placed SHORT order: Size={position_size} @ {entry_price:.2f} (SL: {stop_loss:.2f}, TP: {take_profit:.2f})")

    def notify_trade(self, trade):
        # This method will print information when a trade closes.
        if trade.isclosed:
            print(f"🌙 🚀 Trade closed on {self.data.index[-1]}. PnL: {trade.pl:.2f} | Net Profit: {trade.pnl:.2f}")

# 4. Backtest Execution Order 🚀🌙
# Set up the backtest with our strategy and initial equity of 1,000,000
bt = Backtest(
    data,
    AccumulationManipulation,
    cash=1000000,                # Our size should be 1,000,000
    commission=.000,             # No commission for simplicity
    exclusive_orders=True        # Only one trade at a time for clarity
)

# Run the backtest with default parameters first.
stats = bt.run()
# Print full stats and strategy details.
print("\n🌙 Final Backtest Stats:")
print(stats)
print("\n🌙 Strategy Details:")
print(stats._strategy)