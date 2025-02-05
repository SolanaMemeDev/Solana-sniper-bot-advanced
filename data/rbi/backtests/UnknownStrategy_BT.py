#!/usr/bin/env python3
"""
Solana Dev's Backtest AI 🌙
ATR_MeanReversion Strategy Backtesting Implementation
"""

import os
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

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
    
    # Note on parameter optimization: do not optimize array parameters... optimize each individually
    
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
            prev_bar_close = self.data.Close[-2]
            prev_bar_high = self.data.High[-2]
            prev_bar_low = self.data.Low[-2]
            prev_keltner_upper = self.keltner_upper[-2]
            
            # Entry condition for candidate reversal: price breaks above Keltner channel & forms bearish candle (reversal)
            if (prev_bar_high > prev_keltner_upper) and (prev_bar_close < prev_bar_open):
                # Set candidate reversal candle details if not already set
                if self.reversal_candle is None:
                    self.reversal_candle = {
                        "open": prev_bar_open,
                        "high": prev_bar_high,
                        "low": prev_bar_low,
                        "close": prev_bar_close,
                        "atr": self.atr[-2]  # for reference
                    }
                    print(f"🌙🚀 Candidate reversal candle detected at {self.data.datetime[-2]}: {self.reversal_candle}")
        
        # If there is a candidate reversal candle and no open position, look for entry trigger
        if self.reversal_candle is not None and not self.position:
            # Entry trigger: current bar's low reaches or goes below candidate candle's low (simulate a sell stop order)
            if self.data.Low[-1] <= self.reversal_candle["low"]:
                # Calculate stop loss level: just above the reversal candle high
                stop_loss = self.reversal_candle["high"]
                # Entry price is assumed to be the candidate low (simulate worst-case fill)
                entry_price = self.reversal_candle["low"]
                # Risk per trade in dollars
                risk_dollars = self.equity * self.risk_pct
                # For a short trade, risk = (stop_loss - entry_price)
                risk_per_unit = stop_loss - entry_price
                # Avoid division by zero
                if risk_per_unit <= 0:
                    print("🌙😅 Risk per unit is non-positive, skipping trade entry.")
                else:
                    position_size = risk_dollars / risk_per_unit
                    # Make sure size is an integer number of units!
                    position_size = int(round(position_size))
                    
                    # Calculate take profit target based on risk-reward ratio for a short trade:
                    # Profit target = entry_price - risk_reward * (risk per unit)
                    take_profit = entry_price - self.risk_reward * risk_per_unit
                    
                    print(f"🌙🚀 SHORT ENTRY SIGNAL at {dt}: Entry Price = {entry_price:.2f}, Stop Loss = {stop_loss:.2f}, Take Profit = {take_profit:.2f}, Position Size = {position_size} units")
                    
                    # Enter short with defined stop loss and take profit
                    self.position.enter(
                        direction="short",
                        size=position_size,
                        sl=stop_loss,
                        tp=take_profit
                    )
                    
                    # Reset candidate reversal after trade entry
                    self.reversal_candle = None
        
        # If in a short position, check for exit condition: price action reversal invalidates the trade
        if self.position:
            # For a short position, if price goes above the high of the reversal candle, exit the trade.
            if self.reversal_candle is not None:
                candle_high = self.reversal_candle["high"]
            else:
                # Fallback: use previous candle's high if reversal info lost, though ideally stop loss handles this.
                candle_high = self.data.High[-2]
            
            if self.data.High[-1] > candle_high:
                print(f"🌙⚠️ EXIT SIGNAL at {dt}: Price broke above reversal candle high ({candle_high:.2f}). Exiting short position!")
                self.position.close()
                self.reversal_candle = None  # Reset candidate after exit

# ★★★ Main Backtesting & Optimization Execution ★★★
if __name__ == '__main__':
    # Load and clean data
    data = load_and_clean_data(DATA_PATH)
    
    # Create backtest instance with initial cash=1,000,000
    bt = Backtest(
        data,
        ATR_MeanReversion,
        cash=1000000,
        commission=0.0,
        exclusive_orders=True
    )
    
    # ----------------- INITIAL BACKTEST -----------------
    print("🌙✨ Running initial backtest with default parameters... 🚀")
    stats = bt.run()
    print("🌙✨ INITIAL BACKTEST STATS:")
    print(stats)
    print("🌙✨ Strategy parameters used:", stats._strategy)
    
    # Save initial performance plot
    strategy_name = "ATR_MeanReversion_initial"
    chart_file = os.path.join("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/charts", f"{strategy_name}_chart.html")
    print(f"🌙🚀 Saving initial performance chart to: {chart_file}")
    bt.plot(filename=chart_file, open_browser=False)
    
    # ----------------- PARAMETER OPTIMIZATION -----------------
    print("🌙🚀 Now running parameter optimization... ✨")
    # Optimize parameters: multiplier, risk_atr_multiplier, and risk_reward.
    # Note: Ranges are provided as Python ranges (the optimization engine will try each combination)
    opt_stats, opt_params = bt.optimize(
        multiplier=range(2, 4),           # 2 and 3 (default was 2.5)
        risk_atr_multiplier=range(1, 3),    # 1 and 2
        risk_reward=range(1, 3),            # 1 and 2
        maximize='Equity Final [$]'
    )
    
    print("🌙✨ OPTIMIZATION RESULTS:")
    print(opt_stats)
    print("🌙✨ Optimized Strategy Parameters:", opt_params)
    
    # Save optimized performance plot
    strategy_name = "ATR_MeanReversion_optimized"
    chart_file = os.path.join("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/charts", f"{strategy_name}_chart.html")
    print(f"🌙🚀 Saving optimized performance chart to: {chart_file}")
    bt.plot(filename=chart_file, open_browser=False)
    
    print("🌙🚀 Backtesting complete! Keep shining, Solana Dev! ✨")
