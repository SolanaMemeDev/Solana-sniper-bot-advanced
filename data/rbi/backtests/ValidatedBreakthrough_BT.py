#!/usr/bin/env python3
"""
Solana Dev's Backtest AI 🌙 — ValidatedBreakthrough Strategy Backtest Implementation

This script implements the “ValidatedBreakthrough” strategy:
  • Market structure identification via price‐action (validated swing highs/lows)
  • Supply & demand zone re‑entries 
  • Risk/reward management (minimum 2.5:1) with proper position sizing

It uses TA‑Lib for indicator calculations (SMA, swing high/low via MAX/MIN) through the self.I() wrapper.
Remember:
  • Clean and map CSV data columns as required
  • Use int(round(...)) when calculating position sizes
  • Save all performance plots to the specified charts directory with Solana Dev debug prints! 🚀✨

Data file used: 
  /Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv
"""

import os
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

# =========================
# Strategy Class Definition
# =========================
class ValidatedBreakthrough(Strategy):
    # --- Strategy Parameters (for optimization you can vary these ranges) ---
    sma_period  = 50   # Trend detection indicator period (optimize e.g., range(30,40,2))
    lookback    = 20   # Lookback period for swing highs/lows (optimize e.g., range(15,30,5))
    zone_buffer = 0.002  # Price tolerance to reenter a demand/supply zone (0.2%)
    risk_pct    = 0.01   # Risk 1% of equity per trade
    min_rr      = 2.5    # Minimum risk to reward ratio required (2.5:1)
    sl_buffer   = 0.0015 # Extra stop-loss buffer (0.15%)

    def init(self):
        # Calculate SMA using TA‑Lib via self.I() wrapper!
        self.sma = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_period)
        # For swing high/low calculations use TA‑Lib MAX/MIN functions:
        self.recent_high = self.I(talib.MAX, self.data.High, timeperiod=self.lookback)
        self.recent_low  = self.I(talib.MIN, self.data.Low, timeperiod=self.lookback)
        print("🌙 [Solana Dev] Indicators initialized: SMA period = {}, Lookback = {}".
              format(self.sma_period, self.lookback))
    
    def next(self):
        current_price = self.data.Close[-1]
        print("🚀 [Solana Dev] New bar processed – Current Price: {:.2f}".format(current_price))
        
        # Only enter a trade if no active position exists.
        if not self.position:
            # ------------------
            # Check LONG entries
            # ------------------
            if current_price > self.sma[-1]:
                print("✨ [Solana Dev] Uptrend detected – Close {:.2f} > SMA {:.2f}".format(current_price, self.sma[-1]))
                # Validate re-entry into the demand zone (swing low zone)
                if current_price <= self.recent_low[-1] * (1 + self.zone_buffer):
                    entry_price = current_price
                    # Set stop loss a little below the validated demand zone (swing low)
                    stop_loss   = self.recent_low[-1] * (1 - self.sl_buffer)
                    # Take profit at the recent swing high
                    take_profit = self.recent_high[-1]
                    risk = entry_price - stop_loss
                    reward = take_profit - entry_price
                    
                    print("🌙 [Solana Dev] LONG signal details:")
                    print("     • Recent Low: {:.2f} | Recent High: {:.2f}".format(self.recent_low[-1], self.recent_high[-1]))
                    print("     • Entry: {:.2f} | Stop Loss: {:.2f} | TP: {:.2f}".format(entry_price, stop_loss, take_profit))
                    print("     • Calculated Risk: {:.2f} | Reward: {:.2f}".format(risk, reward))
                    
                    if risk <= 0:
                        print("🚀 [Solana Dev] ERROR: Non‐positive risk detected. Skipping LONG trade!")
                    elif reward / risk < self.min_rr:
                        print("🚀 [Solana Dev] RR Ratio {:.2f} below minimum {:.2f}. Skipping LONG trade!".
                              format(reward / risk, self.min_rr))
                    else:
                        # Calculate position size (ensure integer – avoid float orders)
                        position_size = int(round((self.risk_pct * self.equity) / risk))
                        if position_size <= 0:
                            print("🚀 [Solana Dev] Calculated position size is 0. Trade skipped!")
                        else:
                            print("🌙 [Solana Dev] Placing LONG order with size: {}".format(position_size))
                            self.buy(size=position_size, sl=stop_loss, tp=take_profit)
                else:
                    print("🌙 [Solana Dev] Price not within demand zone threshold for LONG entry.")
            
            # -------------------
            # Check SHORT entries
            # -------------------
            elif current_price < self.sma[-1]:
                print("✨ [Solana Dev] Downtrend detected – Close {:.2f} < SMA {:.2f}".format(current_price, self.sma[-1]))
                # Validate re-entry into the supply zone (swing high zone)
                if current_price >= self.recent_high[-1] * (1 - self.zone_buffer):
                    entry_price = current_price
                    # Set stop loss a little above the validated supply zone (swing high)
                    stop_loss   = self.recent_high[-1] * (1 + self.sl_buffer)
                    # Take profit at the recent swing low
                    take_profit = self.recent_low[-1]
                    risk = stop_loss - entry_price
                    reward = entry_price - take_profit
                    
                    print("🌙 [Solana Dev] SHORT signal details:")
                    print("     • Recent High: {:.2f} | Recent Low: {:.2f}".format(self.recent_high[-1], self.recent_low[-1]))
                    print("     • Entry: {:.2f} | Stop Loss: {:.2f} | TP: {:.2f}".format(entry_price, stop_loss, take_profit))
                    print("     • Calculated Risk: {:.2f} | Reward: {:.2f}".format(risk, reward))
                    
                    if risk <= 0:
                        print("🚀 [Solana Dev] ERROR: Non‐positive risk detected. Skipping SHORT trade!")
                    elif reward / risk < self.min_rr:
                        print("🚀 [Solana Dev] RR Ratio {:.2f} below minimum {:.2f}. Skipping SHORT trade!".
                              format(reward / risk, self.min_rr))
                    else:
                        position_size = int(round((self.risk_pct * self.equity) / risk))
                        if position_size <= 0:
                            print("🚀 [Solana Dev] Calculated position size is 0. Trade skipped!")
                        else:
                            print("🌙 [Solana Dev] Placing SHORT order with size: {}".format(position_size))
                            self.sell(size=position_size, sl=stop_loss, tp=take_profit)
                else:
                    print("🌙 [Solana Dev] Price not within supply zone threshold for SHORT entry.")
        else:
            print("🌙 [Solana Dev] Active position exists – Monitoring trade exit conditions...")
            

# ========================
# Main Backtest Execution
# ========================
if __name__ == '__main__':
    # --------------------
    # Data Loading & Cleanup
    # --------------------
    data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
    print("🚀 [Solana Dev] Loading data from: {}".format(data_path))
    data = pd.read_csv(data_path)

    # Clean column names: remove spaces and make lowercase
    data.columns = data.columns.str.strip().str.lower()
    # Drop any “unnamed” columns
    unnamed_cols = [col for col in data.columns if 'unnamed' in col]
    if unnamed_cols:
        print("🌙 [Solana Dev] Dropping unnamed columns: {}".format(unnamed_cols))
        data = data.drop(columns=unnamed_cols)

    # Map columns to proper names: Required: 'Open', 'High', 'Low', 'Close', 'Volume'
    # CSV columns: datetime, open, high, low, close, volume
    data = data.rename(columns={
        "datetime": "Date",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume"
    })
    # Convert Date column to datetime and set as index
    data["Date"] = pd.to_datetime(data["Date"])
    data = data.sort_values("Date")
    data.set_index("Date", inplace=True)
    print("🌙 [Solana Dev] Data cleaning complete – Columns: {}".format(list(data.columns)))
    
    # -------------------------
    # Run initial backtest
    # -------------------------
    strategy_name = "ValidatedBreakthrough"
    initial_cash = 1_000_000   # Size should be 1,000,000 according to requirements
    print("🚀 [Solana Dev] Starting initial backtest with cash: ${}".format(initial_cash))
    
    bt = Backtest(data, ValidatedBreakthrough, cash=initial_cash, commission=0.0)
    stats = bt.run()
    
    print("🌙 [Solana Dev] Initial Backtest Stats:")
    print(stats)
    print("🌙 [Solana Dev] Strategy parameters used: ")
    print(stats._strategy)
    
    # Save the initial performance chart
    charts_dir = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/charts"
    initial_chart_file = os.path.join(charts_dir, f"{strategy_name}_chart.html")
    print("🚀 [Solana Dev] Saving initial performance chart to: {}".format(initial_chart_file))
    bt.plot(filename=initial_chart_file, open_browser=False)
    
    # -------------------------
    # Run parameter optimization
    # -------------------------
    print("🌙 [Solana Dev] Starting parameter optimization ...")
    optimized_bt = bt.optimize(
        sma_period=range(30, 40, 2),   # Optimize SMA period (trend detection)
        lookback=range(15, 30, 5),      # Optimize lookback period (for swing highs/lows)
        maximize='Equity Final [$]'
    )
    
    print("🚀 [Solana Dev] Optimization complete!")
    print("🌙 [Solana Dev] Optimized Backtest Stats:")
    print(optimized_bt)
    print("🌙 [Solana Dev] Optimized Strategy parameters used: ")
    print(optimized_bt._strategy)
    
    # Save the optimized performance chart
    optimized_chart_file = os.path.join(charts_dir, f"{strategy_name}_optimized_chart.html")
    print("🚀 [Solana Dev] Saving optimized performance chart to: {}".format(optimized_chart_file))
    optimized_bt.plot(filename=optimized_chart_file, open_browser=False)
    
    print("✨🌙 [Solana Dev] Backtest execution complete – Keep reaching for the moon! 🚀")
    
# End of File
