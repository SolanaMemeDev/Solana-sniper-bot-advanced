Here's the fixed code without any usage of `backtesting.lib`:

```python
#!/usr/bin/env python3
"""
Solana Dev's Backtest AI 🌙
Strategy: AtrReversion
This strategy uses ATR and Keltner Channels to spot overextended markets and then enters mean‐reversion trades following a 2B price pattern.
Have fun & moon on! 🚀✨
"""

# 1. All necessary imports
import pandas as pd
import talib
import numpy as np
from backtesting import Backtest, Strategy

# 2. Strategy class with indicators, entry/exit logic, and risk management

class AtrReversion(Strategy):
    # Define any configurable parameters here:
    atr_period = 14
    ema_period = 20
    keltner_mult = 2.0
    risk_percent = 0.01  # 1% risk per trade (of the full equity)
    trade_fraction = 0.5  # use half of our normal size for these trades

    def init(self):
        # Use self.I() wrapper for all indicator calculations!
        # Calculate ATR for risk/extension measure
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        # Calculate EMA as the midline for Keltner Channels (can be viewed as a "centerline")
        self.ema = self.I(talib.EMA, self.data.Close, self.ema_period)
        # Create Keltner Channels from EMA and ATR.
        # Upper Channel = EMA + keltner_mult * ATR; Lower Channel = EMA - keltner_mult * ATR.
        self.keltner_upper = self.I(lambda ema, atr: ema + self.keltner_mult * atr, self.ema, self.atr)
        self.keltner_lower = self.I(lambda ema, atr: ema - self.keltner_mult * atr, self.ema, self.atr)
        print("🌙 [INIT] Indicators set up: ATR period =", self.atr_period,
              ", EMA period =", self.ema_period, ", Keltner Multiplier =", self.keltner_mult)

    def next(self):
        # Always use the most recent data point (index -1) and previous candle (index -2) where needed.
        # Only proceed if we have enough history:
        if len(self.data) < max(self.atr_period, self.ema_period) + 2:
            return

        # Debug: print current bar info for Solana Dev debugging 🌙✨
        dt = self.data.index[-1]
        O = self.data.Open[-1]
        H = self.data.High[-1]
        L = self.data.Low[-1]
        C = self.data.Close[-1]
        print(f"🚀 [{dt}] O: {O:.2f}, H: {H:.2f}, L: {L:.2f}, C: {C:.2f}")

        # Only consider new trade entries if we are flat
        if self.position:
            # Exit logic: you might want to exit when price reverts to the EMA midline.
            # For short positions, we exit when price falls below the EMA.
            if self.position.is_short and C < self.ema[-1]:
                print("🌙💥 [EXIT] Short position closed! Price has reverted near the EMA midline.")
                self.position.close()
            # For long positions, exit when price rises above the EMA.
            elif self.position.is_long and C > self.ema[-1]:
                print("🌙💥 [EXIT] Long position closed! Price has reverted near the EMA midline.")
                self.position.close()
            return  # Do not open a new trade while in a position

        # Entry logic for potential reversion trades
        # We examine the previous candle as our "reversal candle"
        prev_open = self.