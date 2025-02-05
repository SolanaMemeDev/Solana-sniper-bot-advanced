Here's the fixed code with all the backtesting.lib imports and functions replaced:

```python
#!/usr/bin/env python3
"""
Solana Dev's Backtest AI 🌙 - GapAdvantage Strategy Backtesting Implementation
This strategy focuses on volatile stocks (or assets) with a gap‐and‐go setup.
It enters when the price pulls back to key support levels such as VWAP and moving averages,
and exits if the price shows early signs of weakness.
Enjoy the Solana Dev debug vibes! 🌙✨🚀
"""

# 1. Imports
import pandas as pd
import numpy as np
import talib
import pandas_ta as pta  # for additional indicators if needed
from backtesting import Backtest, Strategy

# --------------
# Custom Indicator Functions
# --------------

def custom_vwap(high, low, close, volume):
    """
    Calculate cumulative Volume-Weighted Average Price (VWAP).
    VWAP = cumulative(sum(Typical Price * Volume)) / cumulative(sum(Volume))
    Typical Price = (High + Low + Close) / 3
    """
    tp = (high + low + close) / 3.0
    cum_vp = np.cumsum(tp * volume)
    cum_vol = np.cumsum(volume)
    # Avoid division by zero
    vwap = np.where(cum_vol != 0, cum_vp / cum_vol, 0)
    return vwap

# --------------
# Strategy Class
# --------------

class GapAdvantage(Strategy):
    # Risk parameters (can be adjusted)
    risk_pct = 0.01           # risk 1% of equity per trade
    stop_loss_pct = 0.02      # 2% stop loss
    take_profit_pct = 0.03    # 3% take profit
    
    def init(self):
        # Indicators using the self.I() wrapper for proper caching
        # Simple Moving Averages using talib
        self.sma9 = self.I(talib.SMA, self.data.Close, timeperiod=9)
        self.sma50 = self.I(talib.SMA, self.data.Close, timeperiod=50)
        
        # VWAP indicator using a custom function
        self.vwap = self.I(custom_vwap, self.data.High, self.data.Low, self.data.Close, self.data.Volume)
        
        # Debug prints at initialization
        print("🌙✨ [INIT] Indicators loaded: SMA9, SMA50, and VWAP calculated via custom_vwap()!")
        
        # To store trade-dependent levels
        self.entry_price = None
        self.sl = None
        self.tp = None

    def next(self):
        price = self.data.Close[-1]
        current_vwap = self.vwap[-1]
        current_sma9 = self.sma9[-1]
        
        # Debug: Print current price and indicator values
        print(f"🌙🚀 [NEXT] Price: {price:.2f}, VWAP: {current_vwap:.2f}, SMA9: {current_sma9:.2f}")
        
        # Check if we have an open position
        if not self.position:
            # Entry logic:
            # Condition: price has just crossed above VWAP (pullback bounce) after being below.
            # (i.e. yesterday's close was below vwap and today’s close is above vwap)
            if len(self.data.Close) >= 2 and self.data.Close[-2] < self.vwap[-2] and price > current_vwap:
                self.entry_price = price
                # Set stop loss and take profit levels based on entry price
                self.sl = self.entry_price * (1 - self.stop_loss_pct)
                self.tp = self.entry_price * (1 + self.take_profit_pct)
                risk_per_unit