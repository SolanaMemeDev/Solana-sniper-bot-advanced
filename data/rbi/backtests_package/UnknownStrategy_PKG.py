Here is the fixed code with no usage of backtesting.lib and proper Solana Dev themed debug prints:

```python
#!/usr/bin/env python3
"""
Solana Dev's Backtest AI 🌙
ATR_MeanReversion Strategy Backtesting Implementation
"""

import os
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest

# ★★★ Data Loading & Cleaning ★★★
DATA_PATH = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"

def load_and_clean_data(filepath):
    print("🌙✨ Loading data from:", filepath)
    data = pd.read_csv(filepath, parse_dates=["datetime"])
    # Clean column names: remove spaces and lowercase
    data.columns = data.columns.str.strip().str.lower()
    # Drop unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    # Rename required columns to proper case
    rename_map = {
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume"
    }
    data = data.rename(columns=rename_map)
    # Sort by datetime in case it isn't sorted
    data = data.sort_values("datetime").reset_index(drop=True)
    print("🚀 Data loaded and cleaned! Columns:", list(data.columns))
    return data

# ★★★ Strategy Implementation ★★★
class ATR_MeanReversion(Strategy):
    # --- Strategy Parameters (with defaults and optimization ranges) ---
    keltner_period = 20               # Period for SMA and ATR calculation
    multiplier = 2.5                  # Multiplier for Keltner channel width (optimize: range(2,4))
    risk_atr_multiplier = 1           # Multiplier for ATR based stop loss (optimize: range(1,3))
    risk_reward = 2                   # Risk-reward ratio (optimize: range(1,3))
    risk_pct = 0.01                   # Risk percentage of account equity to risk per trade
    
    def init(self):
        print("🌙✨ Initializing ATR_MeanReversion Strategy...")
        # Calculate indicators via self.I wrapper with TA-lib
        self.sma = self.I(talib.SMA, self.data.Close, timeperiod=self.keltner_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.keltner_period)
        # Calculate Keltner Channel Upper Bound: SMA + multiplier * ATR
        self.keltner_upper = self.sma + self.multiplier * self.atr
        # For potential further use, lower channel could be calculated as:
        self.keltner_lower = self.sma - self.multiplier * self.atr
        
        # Container to store candidate reversal candle info
        self.reversal_candle = None
        print("🚀 Indicators initialized! SMA, ATR and Keltner channels ready. 🌙")
    
    def next(self):
        # --- Debug prints for tracing bars ---
        dt = self.data.datetime[-1]
        print(f"🌙 Bar Date/Time: {dt}, Open: {self.data.Open[-1]}, High: {self.data.High[-1]}, Low: {self.data.Low[-1]}, Close: {self.data.Close[-1]}")
        
        # Check for candidate reversal candle formation on previous bar (if enough history exists)
        if len(self.data.Close) >= 2:
            # Index -2 is the previous completed candle
            prev_bar_open = self.data.Open[-2]
            prev_bar_close = self.data.Close[-