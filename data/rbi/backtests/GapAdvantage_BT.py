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
                risk_per_unit = self.entry_price - self.sl
                # Risk amount limited to risk_pct of current equity
                risk_amount = self.equity * self.risk_pct
                raw_size = risk_amount / risk_per_unit
                # Ensure position size is a whole number (integer) of units
                position_size = int(round(raw_size))
                
                # Debug prints for entry signal and risk management calculation
                print(f"🌙✨ [ENTRY SIGNAL] Price crossed above VWAP! Entry Price: {self.entry_price:.2f}")
                print(f"🌙✨ [RISK MGMT] SL set at: {self.sl:.2f}, TP set at: {self.tp:.2f}, Position Size: {position_size}")
                
                # Submit buy order with proper position sizing
                self.buy(size=position_size)
        else:
            # Exit logic:
            # a) If price falls below the stop loss level, exit immediately.
            # b) Alternatively, if close falls below SMA9, consider it a sign of weakness.
            if price <= self.sl:
                print(f"🌙🚀 [EXIT SIGNAL] Price hit stop loss! Current Price: {price:.2f}, SL: {self.sl:.2f}")
                self.position.close()
            elif price >= self.tp:
                print(f"🌙🚀 [EXIT SIGNAL] Price hit take profit! Current Price: {price:.2f}, TP: {self.tp:.2f}")
                self.position.close()
            elif price < current_sma9:
                print(f"🌙🚀 [EXIT SIGNAL] Price dropped below SMA9! Current Price: {price:.2f}, SMA9: {current_sma9:.2f}")
                self.position.close()
            # Else: hold the position.
            
# --------------
# Data Handling and Backtest Execution
# --------------

def load_and_clean_data(filepath):
    print("🌙✨ [DATA] Loading data from file:", filepath)
    data = pd.read_csv(filepath, parse_dates=['datetime'])
    # Clean column names by removing spaces and converting to lower case
    data.columns = data.columns.str.strip().str.lower()
    # Drop any unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    # Rename required columns to match backtesting.py requirements with proper case
    rename_dict = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
    data.rename(columns=rename_dict, inplace=True)
    # Ensure data is sorted
    data.sort_values('datetime', inplace=True)
    data.reset_index(drop=True, inplace=True)
    print("🌙✨ [DATA] Data cleaning completed! Columns available:", list(data.columns))
    return data

if __name__ == '__main__':
    # Data path as specified
    data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
    data = load_and_clean_data(data_path)
    
    # Initialize Backtest with 1,000,000 cash size and a small commission (if desired)
    bt = Backtest(
        data,
        GapAdvantage,
        cash=1000000,
        commission=0.0005,
        exclusive_orders=True
    )
    
    # Run the backtest with default parameters
    print("🌙🚀 [BACKTEST] Starting backtest with GapAdvantage strategy!")
    stats = bt.run()
    
    # Print full stats and strategy details (no plotting as requested)
    print("\n🌙🚀 [STATS] Full Backtest Stats:\n", stats)
    print("\n🌙🚀 [STATS] Strategy Details:\n", stats._strategy)
    
    # End of script
    print("🌙✨ [DONE] Backtesting complete. Solana Dev out! 🚀")
