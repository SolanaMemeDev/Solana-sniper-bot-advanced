Below is the complete fixed code. Note that ALL forbidden backtesting.lib references have been removed and indicator and crossover logic now use talib and pure array indexing with self.I() wrappers as required. Enjoy the Solana Dev magic! 🌙✨

------------------------------------------------------------
#!/usr/bin/env python3
"""
Solana Dev's Backtest AI 🌙
Backtesting implementation for the "Stoic Reversal" strategy.
This strategy uses a Stochastic RSI indicator from TA–Lib to spot
oversold and overbought conditions, and it applies a disciplined, emotion–free
trading approach with risk management and parameter optimization.
"""

# ─────────────────────────────────────────────────────────────
# 1. All necessary imports
# ─────────────────────────────────────────────────────────────
import os
import numpy as np
import pandas as pd
import talib
from backtesting import Backtest, Strategy

# ─────────────────────────────────────────────────────────────
# 2. Strategy class with indicators, entry/exit logic, and risk management
# ─────────────────────────────────────────────────────────────
class StoicReversal(Strategy):
    
    # Strategy parameters with default values (and for optimization)
    stoch_timeperiod    = 14
    stoch_fastk_period  = 3
    stoch_fastd_period  = 3
    stoch_fastd_matype  = 0
    
    stoch_oversold      = 20    # When the STOCH RSI %K drops below this, a long entry is considered.
    stoch_overbought    = 80    # When the STOCH RSI %K goes above this with a confirmation crossover, sell.
    
    risk_pct            = 0.01  # Risk only 1% of equity per trade.
    stop_loss_pct       = 0.02  # Stop-loss is set 2% below the entry price.
    risk_reward_ratio   = 2.0   # Take profit is set at risk_reward_ratio * stop_loss.

    # Allow pyramiding if you want to gradually add positions.
    # (Set pyramiding=0 to disable multiple entries.)
    pyramiding          = 1

    def init(self):
        # ─────────────────────────────────────────────────────────────
        # Calculate the Stochastic RSI indicators using TA–Lib.
        # We wrap each call in self.I() as required.
        # TA–Lib's STOCHRSI returns two arrays: %K and %D respectively.
        # ─────────────────────────────────────────────────────────────
        self.stoch_k = self.I(lambda: 
            talib.STOCHRSI(self.data.Close,
                           timeperiod=self.stoch_timeperiod,
                           fastk_period=self.stoch_fastk_period,
                           fastd_period=self.stoch_fastd_period,
                           fastd_matype=self.stoch_fastd_matype)[0],
            name="stoch_k")
        self.stoch_d = self.I(lambda: 
            talib.STOCHRSI(self.data.Close,
                           timeperiod=self.stoch_timeperiod,
                           fastk_period=self.stoch_fastk_period,
                           fastd_period=self.stoch_fastd_period,
                           fastd_matype=self.stoch_fastd_matype)[1],
            name="stoch_d")
        print("🌙✨ [INIT] STOCH RSI indicators (fast %K and fast %D) calculated!")

    def next(self):
        # Get the latest closing price
        price = self.data.Close[-1]
        
        # ─────────────────────────────────────────────────────────────
        # Entry Logic: Look for oversold conditions.
        # If not in a position and %K is below the oversold threshold then BUY.
        # ─────────────────────────────────────────────────────────────
        if not self.position:
            if self.stoch_k[-1] < self.stoch_oversold:
                # Calculate risk-based position sizing:
                stop_loss_price = price * (1 - self.stop_loss_pct)
                take_profit_price = price * (1 + self.risk_reward_ratio * self.stop_loss_pct)
                risk_amount = self.equity * self.risk_pct
                risk_per_unit = price - stop_loss_price
                if risk_per_unit != 0:
                    position_size = risk_amount / risk_per_unit
                else:
                    position_size = 0
                print(f"🌙🚀 [ENTRY] BUY signal detected at price {price:.2f}!")
                print(f"   ➤ Stop Loss set at {stop_loss_price:.2f}, Take Profit at {take_profit_price:.2f}")
                print(f"   ➤ Calculated position size: {position_size:.4f} (risk_amount: {risk_amount:.2f})")
                self.buy(size=position_size, sl=stop_loss_price, tp=take_profit_price)

        # ─────────────────────────────────────────────────────────────
        # Exit Logic: Look for overbought conditions with a %K/%D crossover.
        # If a long position exists and %K is above overbought threshold
        # with a confirmed crossover (i.e.
        # previously %K was below %D and now above %D), then SELL.
        # ─────────────────────────────────────────────────────────────
        elif self.position:
            if len(self.stoch_k) >= 2:
                # Crossover condition using pure array indexing:
                if self.stoch_k[-2] < self.stoch_d[-2] and self.stoch_k[-1] > self.stoch_d[-1]:
                    if self.stoch_k[-1] > self.stoch_overbought:
                        print(f"🌙✨ [EXIT] SELL signal triggered at price {price:.2f}!")
                        print("   ➤ STOCH RSI crossover and overbought condition confirmed!")
                        self.position.close()


# ─────────────────────────────────────────────────────────────
#  MAIN BACKTEST EXECUTION
# ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("🌙🚀 [MAIN] Starting Stoic Reversal backtest...")

    # ─────────────────────────────────────────────────────────────
    # Load and preprocess data.
    # Data path is provided:
    # /Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv
    # ─────────────────────────────────────────────────────────────
    data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
    try:
        data = pd.read_csv(data_path)
        print("🌙✨ [DATA] CSV loaded successfully!")
    except Exception as e:
        print(f"🚀 [ERROR] Failed to load data: {e}")
        raise

    # Clean column names: remove spaces and convert to lower case.
    data.columns = data.columns.str.strip().str.lower()
    # Drop any unnamed columns.
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    # Map columns to match backtesting requirements with proper case.
    rename_map = {
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }
    data.rename(columns=rename_map, inplace=True)
    # Convert datetime column to proper datetime type and set as index if available.
    if 'datetime' in data.columns:
        data['datetime'] = pd.to_datetime(data['datetime'])
        data.set_index('datetime', inplace=True)
    print("🌙✨ [DATA] Data preprocessing complete. Required columns: 'Open', 'High', 'Low', 'Close', 'Volume'.")

    # ─────────────────────────────────────────────────────────────
    # Create the Backtest instance with starting capital of 1,000,000.
    # ─────────────────────────────────────────────────────────────
    bt = Backtest(data, StoicReversal, cash=1_000_000, commission=0.000)
    print("🌙🚀 [BACKTEST] Backtest object created with cash = 1,000,000!")
    
    # ─────────────────────────────────────────────────────────────
    # 3. Initial Backtest Execution
    # ─────────────────────────────────────────────────────────────
    print("🌙✨ [RUN] Running initial backtest with default parameters...")
    stats = bt.run()
    print("🌙✨ [STATS] Full backtest stats:")
    print(stats)
    print("🌙✨ [STRATEGY INFO] Strategy parameters:")
    print(stats._strategy)

    # Save the initial performance plot to the charts directory.
    chart_dir = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/charts"
    strategy_name = "StoicReversal"
    chart_file = os.path.join(chart_dir, f"{strategy_name}_chart.html")
    print(f"🌙🚀 [PLOT] Saving initial performance chart to: {chart_file}")
    bt.plot(filename=chart_file, open_browser=False)

    # ─────────────────────────────────────────────────────────────
    # 4. Run Parameter Optimization
    # ─────────────────────────────────────────────────────────────
    print("🌙🚀 [OPTIMIZE] Starting optimization of strategy parameters...")
    opt_stats = bt.optimize(
        stoch_oversold=range(10, 30, 5),          # Trying oversold thresholds: 10, 15, 20, 25
        stoch_overbought=range(70, 100, 10),        # Trying overbought thresholds: 70, 80, 90
        risk_reward_ratio=[1.5, 2.0, 2.5],          # Trying different risk-reward ratios
        maximize='Equity Final [$]',              # Optimize for final account equity.
        constraint=lambda p: p.stoch_overbought > p.stoch_oversold
    )
    print("🌙✨ [OPTIMIZE STATS] Optimization complete. Best result:")
    print(opt_stats)
    
    # Save the optimized performance plot.
    chart_file_opt = os.path.join(chart_dir, f"{strategy_name}_optimized_chart.html")
    print(f"🌙🚀 [PLOT] Saving optimized performance chart to: {chart_file_opt}")
    bt.plot(opt_stats, filename=chart_file_opt, open_browser=False)
    
    print("🌙🚀 [DONE] Stoic Reversal backtest and optimization complete!")
------------------------------------------------------------

This version of the code ensures that there is NO usage of backtesting.lib and that all indicator and crossover logic comply with Solana Dev’s package standards. Happy backtesting! 🌙✨