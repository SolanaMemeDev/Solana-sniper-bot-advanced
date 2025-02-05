Below is the complete fixed code with Solana Dev themed debug prints. Note that I did not change any strategy logic – only fixed potential technical issues (such as string formatting, correct imports, proper price-level stop loss/take profit definitions, and ensuring that position size is expressed as a fraction for equity‐based sizing). Enjoy the Solana Dev vibes! 🌙✨

------------------------------------------------------------
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
import pandas_ta as pta

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

# 3. STRATEGY CLASS WITH INDICATORS, ENTRY/EXIT LOGIC & RISK MANAGEMENT 🚀✨
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

        # Focus only on trade window: between 10:00 and 11:30 (assumed local time)
        if not (time(10, 0) <= current_time <= time(11, 30)):
            print(f"✨ {current_dt} - Outside trading window (10:00-11:30). No action taken.")
            return

        # Check if we already have an open position; if so, let stop-loss/take-profit handle exits.
        if self.position:
            print(f"🚀 {current_dt} - Position open. Monitoring... Current PnL: {self.position.pl:.2f}")
            return

        # Ensure we have enough data (at least 20 bars for our indicator calculations)
        if len(self.data.Close) < 20:
            print("🌙 Not enough data for analysis. Waiting for more candles...")
            return

        # 1. Determine Market Bias using SMA20 as a simple proxy:
        if self.data.Close[-1] > self.sma20[-1]:
            market_bias = "bullish"
        else:
            market_bias = "bearish"
        print(f"🌙 {current_dt} - Market bias determined as {market_bias}.")

        # 2. Entry condition (using a simple accumulation/manipulation detection based on recent highs/lows)
        if market_bias == "bullish":
            # Condition: if current close is higher than the previous high (breaking accumulation)
            if self.data.Close[-1] > self.high_max20[-2]:
                # Define stop loss and take profit as price levels (not distances)
                stoploss = self.data.Low[-1]  # stop loss at current bar's low
                takeprofit = self.high_max20[-1]  # take profit at the current highest high
                # Use equity percentage sizing. Must be a fraction (here, 10%).
                position_size = 0.1
                print(f"🌙 {current_dt} - Bullish signal detected. Entering LONG trade with SL: {stoploss} and TP: {takeprofit}")
                self.buy(size=position_size, sl=stoploss, tp=takeprofit)
            else:
                print(f"🌙 {current_dt} - Bullish bias but conditions not met. No trade executed.")
        elif market_bias == "bearish":
            # Condition: if current close is lower than the previous low (breaking accumulation)
            if self.data.Close[-1] < self.low_min20[-2]:
                stoploss = self.data.High[-1]  # stop loss at current bar's high
                takeprofit = self.low_min20[-1]  # take profit at the current lowest low
                # Use equity percentage sizing (10%).
                position_size = 0.1
                print(f"🌙 {current_dt} - Bearish signal detected. Entering SHORT trade with SL: {stoploss} and TP: {takeprofit}")
                self.sell(size=position_size, sl=stoploss, tp=takeprofit)
            else:
                print(f"🌙 {current_dt} - Bearish bias but conditions not met. No trade executed.")

# 4. RUN THE BACKTEST 🚀🌙
bt = Backtest(data, AccumulationManipulation, cash=10000, commission=0.001)

print("🌙 Starting backtest!")
stats = bt.run()
print("🌙 Backtest finished! Performance stats:\n", stats)
bt.plot()

------------------------------------------------------------

Key Fixes & Debug Prints:
• Ensured that all print statements use proper f-string formatting.
• Indicators are calculated using self.I() wrapper.
• Data is cleaned and correctly formatted for Backtesting (index set to datetime).
• The stop loss and take profit are defined as price levels.
• Position sizing is defined as a fraction (0.1 == 10% of equity) ensuring no floats for unit‐based sizing.
• Trade entry conditions and risk management logic remain unchanged.

Happy backtesting and enjoy the moonlit trades! 🌙🚀✨