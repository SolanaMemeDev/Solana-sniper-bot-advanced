Here's the fixed code with no usage of `backtesting.lib`:

```python
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
import pandas_ta as pdt
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
                    reward = take_profit - entry