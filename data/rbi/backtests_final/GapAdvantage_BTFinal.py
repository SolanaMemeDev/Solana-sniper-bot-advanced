Below is the complete, fixed code with Solana Dev debug prints. The only changes are technical fixes (syntax, scoping, imports, rounding of position sizes, and ensuring stop loss/take profit are absolute levels) while the core strategy logic remains unchanged. Enjoy – Solana Dev Debug AI has landed! 🌙✨

------------------------------------------------------------
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
import math

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
    # Risk parameters (DO NOT CHANGE)
    risk_pct = 0.01           # risk 1% of equity per trade
    stop_loss_pct = 0.02      # 2% stop loss
    take_profit_pct = 0.03    # 3% take profit
    
    def init(self):
        # Indicators using the self.I() wrapper for proper caching
        # SMA indicators using TA-Lib
        self.sma9 = self.I(talib.SMA, self.data.Close, timeperiod=9)
        self.sma50 = self.I(talib.SMA, self.data.Close, timeperiod=50)
        
        # VWAP indicator using our custom function
        self.vwap = self.I(custom_vwap, self.data.High, self.data.Low, self.data.Close, self.data.Volume)
        print("🌙✨ [INIT] Indicators loaded: SMA9, SMA50, and VWAP calculated via custom_vwap()!")
        
        # To store trade-dependent levels
        self.entry_price = None
        self.sl = None
        self.tp = None

    def next(self):
        price = self.data.Close[-1]
        current_vwap = self.vwap[-1]
        current_sma9 = self.sma9[-1]
        print(f"🌙🚀 [NEXT] Price: {price:.2f}, VWAP: {current_vwap:.2f}, SMA9: {current_sma9:.2f}")
        
        # If not in a current position, check entry conditions.
        if not self.position:
            # Entry logic:
            # Condition: price has just crossed above VWAP (pullback bounce) after being below.
            if len(self.data.Close) >= 2 and self.data.Close[-2] < self.vwap[-2] and price > current_vwap:
                self.entry_price = price
                # Set stop loss and take profit levels based on entry price (absolute price levels)
                self.sl = self.entry_price * (1 - self.stop_loss_pct)
                self.tp = self.entry_price * (1 + self.take_profit_pct)
                # Calculate risk per unit (the difference between entry price and stop loss)
                risk_per_unit = abs(self.entry_price - self.sl)
                # Calculate position size based on risk percentage and current equity.
                # NOTE: Must adhere to either fractional sizing or integer units.
                position_size = (self.risk_pct * self.equity) / risk_per_unit
                if position_size >= 1:
                    # Use whole number units (rounded down) if computed size is at least 1 unit.
                    position_size = math.floor(position_size)
                else:
                    # If less than 1 unit - represent as a fraction of equity
                    position_size = self.risk_pct
                # Enter trade with position size, stop loss, and take profit as absolute price levels.
                self.buy(size=position_size, sl=self.sl, tp=self.tp)
                print(f"🌙✨ [ENTRY] Enter trade at {self.entry_price:.2f}, SL at {self.sl:.2f}, TP at {self.tp:.2f}, Size: {position_size}")
        else:
            # Exit logic: exit if price hits stop loss or take profit levels.
            if price <= self.sl or price >= self.tp:
                self.position.close()
                print(f"🌙🚀 [EXIT] Close trade at {price:.2f} (SL: {self.sl:.2f}, TP: {self.tp:.2f})")

# --------------
# Main Backtest Execution
# --------------

if __name__ == '__main__':
    import yfinance as yf
    symbol = "AAPL"
    start_date = "2020-01-01"
    end_date = "2020-12-31"
    
    print("🌙✨ [MAIN] Downloading data for", symbol)
    data = yf.download(symbol, start=start_date, end=end_date)
    print("🌙✨ [MAIN] Data downloaded. Starting backtest...")
    
    bt = Backtest(data, GapAdvantage, cash=100000, commission=0.002)
    stats = bt.run()
    
    print("🌙✨ [MAIN] Backtest completed. Stats:")
    print(stats)
    
    bt.plot()  # Optional: plots the backtest results
------------------------------------------------------------

Solana Dev Debug AI 🌙 has fixed the technical issues – Happy Backtesting and may the Moon guide your trades!