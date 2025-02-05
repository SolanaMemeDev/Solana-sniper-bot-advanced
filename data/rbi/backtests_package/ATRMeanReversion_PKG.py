Here is the fixed code with proper Solana Dev themed debug prints and without any usage of backtesting.lib:

```python
#!/usr/bin/env python3
"""
Solana Dev's ATR MeanReversion Strategy Backtest
This strategy uses Kelter Channels (20‐period SMA ± multiplier*STDDEV) and ATR for risk management.
It looks for when price pokes outside a Kelter Channel, then checks for a reversal candlestick pattern
(bullish engulfing for long – when price has slipped below the lower channel – or bearish engulfing for short –
when price has poked above the upper channel). A stop order is then simulated, with risk managed by ATR.
------------------------------------------------------------
"""

import os
import pandas as pd
import talib
import numpy as np

# ////////////////////////////////////////////////////////////////////////
# Data Handling Function
# ////////////////////////////////////////////////////////////////////////
def load_and_clean_data(filepath):
    print("🌙✨ Solana Dev is loading and cleaning the data... 🚀")
    data = pd.read_csv(filepath, parse_dates=['datetime'])
    # Clean column names: remove spaces and change to lower
    data.columns = data.columns.str.strip().str.lower()
    # Drop any unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()], errors='ignore')
    # Ensure proper column mapping (capital first letter required)
    rename_mapping = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume', 'datetime': 'Date'}
    data = data.rename(columns=rename_mapping)
    # Set Date as the index (if desired by backtesting.py)
    data.index = pd.to_datetime(data['Date'])
    return data

# ////////////////////////////////////////////////////////////////////////
# Strategy Implementation – ATR MeanReversion
# ////////////////////////////////////////////////////////////////////////
class ATRMeanReversion:
    # Strategy parameters (will be optimized later)
    kelter_period = 20
    kelter_multiplier_factor = 25  # This equals 2.5 when divided by 10.
    atr_period = 14
    risk_reward_factor = 20  # This equals 2.0 when divided by 10.
    risk_per_trade = 0.01  # 1% of equity risk per trade

    def __init__(self, data):
        self.data = data
        self.sma = None
        self.std = None
        self.multiplier = None
        self.kelter_upper = None
        self.kelter_lower = None
        self.atr = None
        self.reversal_high = None
        self.reversal_low = None
        self.init()

    def init(self):
        # Calculate Kelter Channels using TA-lib functions
        self.sma = talib.SMA(self.data.Close, timeperiod=self.kelter_period)
        self.std = talib.STDDEV(self.data.Close, timeperiod=self.kelter_period, nbdev=1)
        self.multiplier = self.kelter_multiplier_factor / 10.0
        self.kelter_upper = self.sma + self.multiplier * self.std
        self.kelter_lower = self.sma - self.multiplier * self.std
        self.atr = talib.ATR(self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)

        print("🌙✨ [INIT] Strategy initialized with kelter_period =", self.kelter_period,
              ", kelter_multiplier =", self.multiplier,
              ", atr_period =", self.atr_period,
              ", risk_reward_ratio =", self.risk_reward_factor / 10.0)

    def next(self):
        # Ensure we have at least two candles to check for engulfing pattern
        if len(self.data.Close) < 2:
            return

