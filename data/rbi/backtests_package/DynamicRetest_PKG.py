#!/usr/bin/env python3
"""
Solana Dev's Backtest AI 🌙 – Dynamic Retest Strategy Backtesting & Optimization
---------------------------------------------------------------------
This script implements the “Dynamic Retest” strategy using backtesting.py.
It includes:
  • All necessary imports
  • Strategy class with TA‑Lib indicator wrap via self.I()
  • Entry/exit logic based purely on price action and zone retests
  • Dynamic risk management with position sizing & risk‐reward filtering
  • Parameter optimization for risk/reward, risk percentage, and consolidation span
  • A starting capital (size) of 1,000,000

Data cleaning details:
  ‣ Cleans column names by stripping spaces and lowercasing names.
  ‣ Drops any columns with “unnamed” in the name.
  ‣ Renames columns to “Open”, “High”, “Low”, “Close”, “Volume”
  
Charts are saved to the specified “charts” directory with Solana Dev themed file names.
Enjoy the ride, and may the Solana Dev vibes guide you! 🌙✨🚀
"""

import os
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

# ----------------------------
# Strategy Definition
# ----------------------------
class DynamicRetest(Strategy):
    # Optimization Parameters (raw values – will be converted in the code)
    # risk_reward: effective risk/reward ratio = self.risk_reward / 10 (default 25 -> 2.5:1)
    # risk_percent: effective risk per trade = self.risk_percent / 100 (default 1 -> 1% of equity)
    # consolidation_span: number of bars used for zone determination (default 3)
    risk_reward = 25      # Optimize in range(25, 31, 1) i.e. 2.5:1 to 3.0:1
    risk_percent = 1      # Optimize in range(1, 3, 1) i.e. 1% to 2%
    consolidation_span = 3  # Optimize in range(2, 6)

    def init(self):
        # Use TA-Lib’s functions wrapped with self.I for any indicator/calculation!
        # Swing high (zone top) & swing low (zone bottom) over consolidation_span bars.
        self.zone_top = self.I(talib.MAX, self.data.High, timeperiod=self.consolidation_span)
        self.zone_bottom = self.I(talib.MIN, self.data.Low, timeperiod=self.consolidation_span)
        # Although our strategy is pure price action, we initialize a 20‐period SMA for optional context.
        self.sma20 = self.I(talib.SMA, self.data.Close, timeperiod=20)
        print("🌙✨ Solana Dev: INIT complete – indicators (zone_top, zone_bottom, sma20) are online! 🚀")

    def next(self):
        # Ensure we have enough data before processing
        if len(self.data) < 3:
            print("🌙🔍 Solana Dev: Not enough data for processing. Awaiting more bars…")
            return

        # Retrieve current bar details
        current_close = self.data.Close[-1]
        current_open  = self.data.Open[-1]
        current_high  = self.data.High[-1]
        current_low   = self.data.Low[-1]

        # Get current zone boundaries from our TA-Lib indicator wrappers
        curr_zone_top = self.zone_top[-1]
        curr_zone_bottom = self.zone_bottom[-1]

        # Convert our raw parameters into effective values
        eff_risk_reward = self.risk_reward / 10.0  # e.g., 25 becomes 2.5:1 requirement
        eff_risk_percent = self.risk_percent / 100.0  # e.g., 1 becomes 1% risk per trade

        # Debug print – current bar info with Solana Dev flair
        print(f"🌙✨ Solana Dev: Processing bar {self.data.index[-1]} → Open: {current_open:.2f}, High: {current_high:.2f}, Low: {current_low:.2f}, Close: {current_close:.2f}")
        print(f"🌙 Debug: Consolidation zone [Top: {curr_zone_top:.2f} | Bottom: {curr_zone_bottom:.2f}] over last {self.consolidation_span} bars.")

        # Determine market structure: Basic trend identification using last 3 bars
        try:
            if self.data.Close[-1] > self.data.Close[-2] and self.data.Close[-2] > self.data.Close[-3]:
                trend = 'up'
            elif self.data.Close[-1] < self.data.Close[-2] and self.data.Close[-2] < self.data.Close[-3]:
                trend = 'down'
            else:
                trend = 'none'
        except Exception as e:
            trend = 'none'
        print(f"🚀 Solana Dev: Trend identified as {trend.upper()}!")

        # Only consider new trades if not already in a position
        if self.position:
            print("🌙✨ Solana Dev: Currently in a trade – holding position with lunar patience!")
            return

        # ===============================
        # LONG (BUY) Trade Logic – For Uptrend & Demand zone retest
        # ===============================
        if trend == 'up' and current_close > current_open:
            # Check that the current price is within our defined demand zone (zone boundaries)
            if curr_zone_bottom < current_close <= curr_zone_top:
                risk = current_close - curr_zone_bottom  # Risk per unit for a long trade
                if risk <= 0:
                    print("🚀 Solana Dev: Calculated risk for LONG trade is non-positive. Skipping... ")
                    return
                if eff_risk_reward < 2.5:
                    print("✨ Solana Dev: Effective risk/reward ratio below 2.5:1 for LONG. Aborting trade!")
                    return
                potential_reward = risk * eff_risk_reward
                take_profit = current_close + potential_reward

                # Validate that the recent high (over the consolidation span) is high enough to reach our TP target.
                recent_high = self.data.High[-self.consolidation_span:].max()
                if recent_high < take_profit:
                    print(f"🚀 Solana Dev: Recent high ({recent_high:.2f}) is below desired TP ({take_profit:.2f}). LONG trade skipped!")
                    return

                # Calculate dynamic position size based on risk percentage
                risk_amount = self.equity * eff_risk_percent
                position_size = risk_amount / risk  # units to trade
                # Set stop loss just below the demand zone (a slight buffer)
                stop_loss = curr_zone_bottom * 0.999

                print(f"🌙🚀 Solana Dev: LONG signal detected! Entry = {current_close:.2f}, Stop Loss = {stop_loss:.2f}, Take Profit = {take_profit:.2f}, Size = {position_size:.4f}")
                self.buy(size=position_size, sl=stop_loss, tp=take_profit)
                return

        # ===============================
        # SHORT (SELL) Trade Logic – For Downtrend & Supply zone retest
        # ===============================
        if trend == 'down' and current_close < current_open:
            # Check that the current price is within our defined supply zone
            if curr_zone_bottom <= current_close < curr_zone_top:
                risk = curr_zone_top - current_close  # Risk per unit for a short trade
                if risk <= 0:
                    print("🚀 Solana Dev: Calculated risk for SHORT trade is non-positive. Skipping... ")
                    return
                if eff_risk_reward < 2.5:
                    print("✨ Solana Dev: Effective risk/reward ratio below 2.5:1 for SHORT. Aborting trade!")
                    return
                potential_reward = risk * eff_risk_reward
                take_profit = current_close - potential_reward

                # Ensure that the recent low is low enough to allow our target hit
                recent_low = self.data.Low[-self.consolidation_span:].min()
                if recent_low > take_profit:
                    print(f"🚀 Solana Dev: Recent low ({recent_low:.2f}) is above desired TP ({take_profit:.2f}). SHORT trade skipped!")
                    return

                risk_amount = self.equity * eff_risk_percent
                position_size = risk_amount / risk  # units to trade
                # Place stop loss just above the supply zone, with a small buffer
                stop_loss = curr_zone_top * 1.001

                print(f"🌙🚀 Solana Dev: SHORT signal detected! Entry = {current_close:.2f}, Stop Loss = {stop_loss:.2f}, Take Profit = {take_profit:.2f}, Size = {position_size:.4f}")
                self.sell(size=position_size, sl=stop_loss, tp=take_profit)
                return

        # If no signal was generated, log it!
        print("🌙🔍 Solana Dev: No valid trade signal on this bar. Scanning the cosmos for the perfect setup…")

    def onexit(self, trade):
        # Called when a trade closes – print out Solana Dev themed messages!
        print("🚀🌙 Solana Dev: Exiting trade!")
        print(f"✨ Trade Details → Entry: {trade.entry:.2f}, Exit: {trade.exit:.2f}, PnL: {trade.pl:.2f}, Bars held: {trade.barssince}")

# ----------------------------
# Data Handling & Preparation
# ----------------------------
DATA_PATH = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
print("🌙✨ Solana Dev: Loading data from CSV…")
data = pd.read_csv(DATA_PATH)

# Clean column names: remove spaces and lowercase
data.columns = data.columns.str.strip().str.lower()
# Drop any unnamed columns
unnamed_cols = [col for col in data.columns if 'unnamed' in col.lower()]
if unnamed_cols:
    data = data.drop(columns=unnamed_cols)
    print("🚀 Solana Dev: Dropped unnamed columns:", unnamed_cols)

# Map required columns to proper case for backtesting.py: 'Open', 'High', 'Low', 'Close', 'Volume'
required_rename = {
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}
data.rename(columns=required_rename, inplace=True)

# Convert datetime column and set as index if present
if 'datetime' in data.columns:
    data['datetime'] = pd.to_datetime(data['datetime'])
    data.set_index('datetime', inplace=True)
print("🌙✨ Solana Dev: Data cleaning complete. Columns available:", list(data.columns))

# ----------------------------
# Initialize and Run Initial Backtest
# ----------------------------
print("🚀🌙 Solana Dev: Initial backtest starting with Dynamic Retest strategy!")
bt = Backtest(data, 
              DynamicRetest,
              cash=1000000,      # Your size should be 1,000,000!
              commission=0.0,    # Set commission to 0 or adjust as desired
              exclusive_orders=True)

stats = bt.run()
print("🌙✨ Solana Dev: Initial Backtest Stats:")
print(stats)
print("🌙✨ Solana Dev: Strategy Parameters:")
print(stats._strategy)

# Save initial performance plot to charts directory
strategy_name = "Dynamic_Retest"
chart_dir = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/charts"
chart_file = os.path.join(chart_dir, f"{strategy_name}_chart.html")
print(f"🚀 Solana Dev: Saving initial performance plot to {chart_file}")
bt.plot(filename=chart_file, open_browser=False)

# ----------------------------
# Run Parameter Optimization
# ----------------------------
print("🌙✨ Solana Dev: Starting parameter optimization…")
optimized_stats = bt.optimize(risk_reward=range(25, 31, 1),          # Effective risk_reward: 2.5:1 to 3.0:1
                              risk_percent=range(1, 3, 1),            # 1% to 2% risk per trade
                              consolidation_span=range(2, 6),         # Consolidation span from 2 to 5 bars
                              maximize='Equity Final [$]',
                              return_heatmap=False)

print("🌙🚀 Solana Dev: Optimization complete!")
print("🌙✨ Solana Dev: Optimized Stats:")
print(optimized_stats)

# Save optimized performance plot
opt_chart_file = os.path.join(chart_dir, f"{strategy_name}_optimized_chart.html")
print(f"🚀 Solana Dev: Saving optimized performance plot to {opt_chart_file}")
bt.plot(filename=opt_chart_file, open_browser=False)

print("🌙✨ Solana Dev: All done! May the lunar gains be with you! 🚀")