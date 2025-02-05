Below is the complete backtesting.py implementation for the StochasticPhaseTrader strategy. Copy and run the code (after installing required packages such as backtesting, talib, pandas, etc.) and enjoy Solana Dev’s witty debug prints! 🌙✨🚀

--------------------------------------------------
#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

# ─── CUSTOM STOCHASTIC RSI FUNCTION ──────────────────────────────
def stochrsi_func(close, period, fastk_period, fastd_period):
    # Calculate RSI first
    rsi = talib.RSI(close, timeperiod=period)
    # Compute the lowest and highest RSI over the lookback period
    min_rsi = talib.MIN(rsi, timeperiod=period)
    max_rsi = talib.MAX(rsi, timeperiod=period)
    # Avoid divide-by-zero issues
    stoch_rsi = 100 * ((rsi - min_rsi) / (max_rsi - min_rsi + 1e-10))
    # Smooth the stoch_rsi with an SMA to get %K and again for %D
    fastk = talib.SMA(stoch_rsi, timeperiod=fastk_period)
    fastd = talib.SMA(fastk, timeperiod=fastd_period)
    return fastk, fastd

# ─── STRATEGY CLASS ───────────────────────────────────────────────
class StochasticPhaseTrader(Strategy):
    # Default indicator and risk parameters:
    period = 14                    # Lookback period for RSI in StochRSI
    fastk_period = 3               # Smoothing for fast %K
    fastd_period = 3               # Smoothing for fast %D
    oversold = 20                  # Oversold threshold (buy signal)
    overbought = 80                # Overbought threshold (sell signal)
    risk_percent = 0.01            # Risk 1% of equity per trade
    sl_pct = 0.02                  # Stop loss set at 2% below entry price

    def init(self):
        # Calculate Stochastic RSI indicator using our custom function and self.I() wrapper.
        # (self.I() caches the indicator output so that it is only computed once.)
        self.stochk, self.stochd = self.I(stochrsi_func, self.data.Close,
                                          self.period, self.fastk_period, self.fastd_period)
        # Save the last buy's stoch RSI value for DCA decisions.
        self.last_buy_stoch = None
        print("🌙✨ [INIT] StochasticPhaseTrader initialized with parameters:")
        print(f"      period={self.period}, fastk_period={self.fastk_period}, fastd_period={self.fastd_period}")
        print(f"      oversold threshold={self.oversold}, overbought threshold={self.overbought}")
        print(f"      risk_percent={self.risk_percent}, sl_pct={self.sl_pct}")
    
    def next(self):
        current_close = self.data.Close[-1]
        current_k = self.stochk[-1]
        # For crossover detection, get the previous candle's stochk value if available
        prev_k = self.stochk[-2] if len(self.stochk) > 1 else current_k
        print(f"🌙✨ [NEXT] Candle @ {self.data.index[-1]} | Close: {current_close:.2f} | StochK: {current_k:.2f}")

        # ENTRY SIGNAL: When NOT in a position and the indicator crosses below the oversold threshold
        if not self.position:
            if prev_k > self.oversold and current_k <= self.oversold:
                entry_price = current_close
                stop_loss = entry_price * (1 - self.sl_pct)
                # Calculate risk amount per trade (percentage of our current equity)
                risk_amount = self.equity * self.risk_percent
                risk_per_unit = entry_price - stop_loss
                position_size = risk_amount / risk_per_unit
                # Make sure to round to an integer number of units as required
                position_size = int(round(position_size))
                if position_size < 1:
                    position_size = 1
                print(f"🚀🌙 [ENTRY] BUY signal generated!")
                print(f"      Entry Price: {entry_price:.2f}, Stop Loss: {stop_loss:.2f}, Position Size: {position_size}")
                self.buy(size=position_size, sl=stop_loss)
                # Save the stoch value at entry to help with potential dollar-cost averaging (DCA)
                self.last_buy_stoch = current_k

        else:
            # If already in a position, consider DCA if StochRSI keeps declining
            if self.last_buy_stoch is not None and current_k < self.last_buy_stoch:
                entry_price = current_close
                stop_loss = entry_price * (1 - self.sl_pct)
                risk_amount = self.equity * self.risk_percent
                risk_per_unit = entry_price - stop_loss
                add_size = risk_amount / risk_per_unit
                add_size = int(round(add_size))
                if add_size < 1:
                    add_size = 1
                print(f"🌙🚀 [DCA] Additional BUY signal (DCA) at {entry_price:.2f} with size {add_size}")
                self.buy(size=add_size, sl=stop_loss)
                # Update the last buy indicator to the new lower value.
                self.last_buy_stoch = current_k

            # EXIT SIGNAL: Dollar-cost average OUT when the indicator rises above the overbought threshold
            if prev_k < self.overbought and current_k >= self.overbought:
                print("✨🚀 [EXIT] SELL signal generated! StochK crossed above the overbought threshold.")
                self.position.close()
                self.last_buy_stoch = None

# ─── MAIN BACKTEST EXECUTION ───────────────────────────────────────
if __name__ == '__main__':
    # Data location and load
    data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
    print("🌙✨ [DATA] Loading data from:", data_path)
    data = pd.read_csv(data_path, parse_dates=['datetime'])
    
    # Clean up columns: remove spaces and drop any unnamed columns
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    # Ensure required columns and proper column mapping (capital first letter names)
    data.rename(columns={'open': 'Open', 
                         'high': 'High', 
                         'low': 'Low', 
                         'close': 'Close', 
                         'volume': 'Volume',
                         'datetime': 'Date'}, inplace=True)
    data.set_index('Date', inplace=True)
    print("🌙✨ [DATA] Data cleaning complete. Columns:", data.columns.tolist())

    # Initialize Backtest with cash size 1,000,000
    bt = Backtest(data, StochasticPhaseTrader, cash=1000000, commission=.000,
                  exclusive_orders=True)

    # ─── INITIAL BACKTEST ─────────────────────────────
    print("🌙✨ [BACKTEST] Running initial backtest with default parameters...")
    stats = bt.run()
    print("🌙✨ [STATS] Full Stats:")
    print(stats)
    print("🌙✨ [STRATEGY DETAILS]:")
    print(stats._strategy)

    # Save the initial performance plot to charts folder
    charts_dir = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/charts"
    os.makedirs(charts_dir, exist_ok=True)
    strategy_name = "StochasticPhaseTrader"
    chart_file_initial = os.path.join(charts_dir, f"{strategy_name}_chart_initial.html")
    print(f"🌙✨ [PLOT] Saving initial performance plot to: {chart_file_initial}")
    bt.plot(filename=chart_file_initial, open_browser=False)

    # ─── PARAMETER OPTIMIZATION ─────────────────────
    print("🌙✨ [OPTIMIZATION] Running parameter optimization... 🚀")
    optimized_stats = bt.optimize(
        oversold=range(15, 25, 5),         # Try oversold thresholds: 15 and 20
        overbought=range(75, 85, 5),         # Try overbought thresholds: 75 and 80
        sl_pct=[0.01, 0.02, 0.03],           # Try stop loss percentages: 1%, 2%, 3%
        maximize='Equity Final [$]',
        constraint=lambda param: param.oversold < param.overbought  # simple constraint
    )
    print("🌙✨ [OPTIMIZATION] Optimized Stats:")
    print(optimized_stats)

    # Save the optimized performance plot to charts folder
    chart_file_optimized = os.path.join(charts_dir, f"{strategy_name}_chart_optimized.html")
    print(f"🌙✨ [PLOT] Saving optimized performance plot to: {chart_file_optimized}")
    bt.plot(filename=chart_file_optimized, open_browser=False)
--------------------------------------------------

Explanation of key points and debugging features:
• All necessary libraries are imported (including os, pandas, numpy, talib, backtesting).
• The strategy uses a custom stochrsi_func with talib functions (RSI, MIN, MAX, SMA) and is called by self.I().
• Debug prints (with plenty of Solana Dev themed emojis 🌙 ✨ 🚀) are included at key stages (data loading, initialization, entry/DCA/exit signals).
• Position sizing is strictly converted to an integer using int(round(...)) so that size is acceptable by backtesting.py.
• Data is cleaned per instructions (trim spaces and proper column name mapping).
• We run an initial backtest and then perform a parameter optimization on oversold, overbought, and sl_pct.
• Finally, performance charts are saved to the specified charts directory.

Happy backtesting and may your trades always be lunar-tastic! 🌙🚀✨