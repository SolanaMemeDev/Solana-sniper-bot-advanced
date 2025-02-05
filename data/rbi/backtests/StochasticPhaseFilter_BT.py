Below is the complete Python script that implements the StochasticPhaseFilter strategy according to the instructions. Copy the code into (for example) a file named backtest_stochastic_phase_filter.py and run it. Enjoy the Solana Dev debugging messages! 🚀🌙✨

────────────────────────────
#!/usr/bin/env python3
import os
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, crossup, crossdown

# ═════════════════════════════════════════════════════════════════════
# Strategy: StochasticPhaseFilter
#
# This strategy uses the Stochastic RSI indicator (calculated via TA‑Lib)
# to identify overbought and oversold conditions. When the smoothed StochRSI
# crosses below the oversold threshold (default 20) we look to buy, and when
# it crosses above the overbought threshold (default 80) we look to sell.
#
# Entry Rules:
#  • If no position exists and the smoothed StochRSI crosses below oversold,
#    calculate a LONG order (enter buy).
#  • If no position exists and the smoothed StochRSI crosses above overbought,
#    calculate a SHORT order (enter sell).
#
# Exit Rules:
#  • Exit LONG positions when the smoothed StochRSI crosses upward (from
#    below) the oversold threshold.
#  • Exit SHORT positions when the smoothed StochRSI crosses downward (from
#    above) the overbought threshold.
#
# Risk Management:
#  • A fraction of total equity is risked on each trade (default 1%).
#  • Stop loss is calculated as a percentage move (default 1%) and
#    take profit is derived from a reward‐to‐risk ratio (default 2).
#  • Position sizing is computed as: position_size = risk_amount / risk_per_unit,
#    then rounded to an integer.
#
# Parameter optimization is included for:
#  • overbought level (default: 80; optimized over 75,80)
#  • oversold level (default: 20; optimized over 15,20)
#  • stop_loss_pct (in %, default: 1; optimized over 1,2,3)
#  • reward_risk (default: 2; optimized over 1,2,3,4)
#
# IMPORTANT: Data is cleaned and columns are renamed to: Open, High, Low,
# Close, Volume.
#
# Charts (initial and optimized) will be saved in the designated charts directory.
# ═════════════════════════════════════════════════════════════════════

class StochasticPhaseFilter(Strategy):
    # Define strategy parameters (optimization ranges are integers so percentages are in whole numbers)
    overbought  = 80  # overbought threshold (to trigger SELL signals)
    oversold    = 20  # oversold threshold (to trigger BUY signals)
    stop_loss_pct = 1  # stop loss as a percentage of price (1% by default)
    reward_risk  = 2   # reward-to-risk ratio (default: 2)
    risk_pct     = 1   # risk 1% of equity per trade

    def init(self):
        # Calculate RSI, then compute the lowest and highest values over the 14-period window
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.lowest_rsi = self.I(talib.MIN, self.rsi, timeperiod=14)
        self.highest_rsi = self.I(talib.MAX, self.rsi, timeperiod=14)
        # Calculate StochRSI using a custom helper (always wrapped inside self.I())
        self.stoch_rsi = self.I(self.calc_stoch_rsi, self.rsi, self.lowest_rsi, self.highest_rsi)
        # Smooth the StochRSI with a 3-period SMA
        self.stoch_rsi_smoothed = self.I(talib.SMA, self.stoch_rsi, timeperiod=3)
        print("🌙✨ [INIT] Indicators initialized: RSI, StochRSI and smoothed StochRSI.")

    def next(self):
        # Ensure we have enough history for cross detection
        if len(self.data) < 2:
            return

        current_close = self.data.Close[-1]
        stoch  = self.stoch_rsi_smoothed[-1]
        prev_stoch = self.stoch_rsi_smoothed[-2]
        bar_time = self.data.index[-1]

        # Solana Dev themed debug print for every new bar!
        print(f"🌙✨ [BAR] {bar_time} | Close: {current_close:.2f} | StochRSI: {stoch:.2f}")

        # ENTRY LOGIC (when no open position)
        if not self.position:
            # LONG ENTRY: When the StochRSI crosses below the oversold level
            if prev_stoch >= self.oversold and stoch < self.oversold:
                # Calculate stop loss and position sizing for LONG trades
                stop_loss_price = current_close * (1 - self.stop_loss_pct/100)
                risk_per_unit = current_close - stop_loss_price
                risk_amount = self.equity * (self.risk_pct/100)
                if risk_per_unit <= 0:
                    print("🌙🚀 [LONG] Warning: risk per unit non-positive. Skipping long entry!")
                else:
                    position_size = int(round(risk_amount / risk_per_unit))
                    take_profit_price = current_close + risk_per_unit * self.reward_risk
                    print(f"🌙🚀 [LONG] BUY signal! Price: {current_close:.2f} | StochRSI drop from {prev_stoch:.2f} to {stoch:.2f}")
                    print(f"🌙🚀 [LONG] Position size: {position_size} units | SL: {stop_loss_price:.2f} | TP: {take_profit_price:.2f}")
                    self.buy(size=position_size, sl=stop_loss_price, tp=take_profit_price)

            # SHORT ENTRY: When the StochRSI crosses above the overbought level
            elif prev_stoch <= self.overbought and stoch > self.overbought:
                # Calculate stop loss and position sizing for SHORT trades
                stop_loss_price = current_close * (1 + self.stop_loss_pct/100)
                risk_per_unit = stop_loss_price - current_close
                risk_amount = self.equity * (self.risk_pct/100)
                if risk_per_unit <= 0:
                    print("🌙🚀 [SHORT] Warning: risk per unit non-positive. Skipping short entry!")
                else:
                    position_size = int(round(risk_amount / risk_per_unit))
                    take_profit_price = current_close - risk_per_unit * self.reward_risk
                    print(f"🌙🚀 [SHORT] SELL signal! Price: {current_close:.2f} | StochRSI rise from {prev_stoch:.2f} to {stoch:.2f}")
                    print(f"🌙🚀 [SHORT] Position size: {position_size} units | SL: {stop_loss_price:.2f} | TP: {take_profit_price:.2f}")
                    self.sell(size=position_size, sl=stop_loss_price, tp=take_profit_price)

        else:
            # EXIT LOGIC
            # LONG EXIT: When in a long position and StochRSI crosses upward through the oversold level
            if self.position.is_long and prev_stoch < self.oversold and stoch >= self.oversold:
                print(f"🌙✨ [EXIT LONG] StochRSI crossed above {self.oversold} (from {prev_stoch:.2f} to {stoch:.2f}). Closing LONG position.")
                self.position.close()

            # SHORT EXIT: When in a short position and StochRSI crosses downward through the overbought level
            if self.position.is_short and prev_stoch > self.overbought and stoch <= self.overbought:
                print(f"🌙✨ [EXIT SHORT] StochRSI crossed below {self.overbought} (from {prev_stoch:.2f} to {stoch:.2f}). Closing SHORT position.")
                self.position.close()

    @staticmethod
    def calc_stoch_rsi(rsi, lowest, highest):
        """Calculate the Stochastic RSI."""
        epsilon = 1e-10  # avoid division by zero
        return 100 * ((rsi - lowest) / ((highest - lowest) + epsilon))


# ═════════════════════════════════════════════════════════════════════
# MAIN BACKTEST EXECUTION
# ═════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🌙🚀 Solana Dev Backtest AI Initialized for StochasticPhaseFilter Strategy!")

    # Load data from the provided CSV file path
    data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
    try:
        data = pd.read_csv(data_path, parse_dates=["datetime"])
        print("🌙✨ Data loaded successfully!")
    except Exception as e:
        print(f"🌙🚀 Error loading data: {e}")
        exit()

    # Clean column names: remove spaces, convert to lower case
    data.columns = data.columns.str.strip().str.lower()
    # Drop any unnamed columns (if present)
    data = data.drop(columns=[col for col in data.columns if "unnamed" in col.lower()])

    # Rename columns to match backtesting.py requirements (Proper Case)
    rename_map = {
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
        "datetime": "Date"
    }
    data.rename(columns=rename_map, inplace=True)
    # Set Date as the index and then drop the Date column
    if "Date" in data.columns:
        data.index = pd.to_datetime(data["Date"])
        data.drop(columns=["Date"], inplace=True)

    print("🌙✨ Data columns after cleaning and renaming:", list(data.columns))

    # Initialize Backtest with a starting capital (size) of 1,000,000 USD
    bt = Backtest(data, StochasticPhaseFilter, cash=1000000, commission=0.0)

    # ─── INITIAL BACKTEST ────────────────────────────────────────────
    print("🌙🚀 Starting initial backtest with default parameters...")
    stats = bt.run()
    print("🌙🚀 Initial Backtest Stats:")
    print(stats)
    print("🌙🚀 Strategy Parameters:")
    print(stats._strategy)

    # Save the initial performance plot in the charts directory
    strategy_name = "StochasticPhaseFilter"
    chart_dir = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/charts"
    os.makedirs(chart_dir, exist_ok=True)
    chart_file = os.path.join(chart_dir, f"{strategy_name}_chart.html")
    bt.plot(filename=chart_file, open_browser=False)
    print(f"🌙🚀 Initial performance chart saved to: {chart_file}")

    # ─── OPTIMIZATION ────────────────────────────────────────────────
    print("🌙🚀 Starting optimization of parameters...")
    opt_stats = bt.optimize(
        overbought=range(75, 85, 5),      # Test values: 75 and 80
        oversold=range(15, 25, 5),         # Test values: 15 and 20
        stop_loss_pct=range(1, 4),         # Test stop loss percentages: 1, 2 and 3 (%)
        reward_risk=range(1, 5),           # Test reward/risk ratios: 1, 2, 3 and 4
        risk_pct=[1],                    # Fixed risk percentage: 1%
        maximize='Equity Final [$]',
        return_stats=True
    )
    print("🌙🚀 Optimization complete! Optimized Stats:")
    print(opt_stats)

    # Save the optimized performance plot in the charts directory
    optimized_chart_file = os.path.join(chart_dir, f"{strategy_name}_optimized_chart.html")
    bt.plot(filename=optimized_chart_file, open_browser=False)
    print(f"🌙🚀 Optimized performance chart saved to: {optimized_chart_file}")

    print("🌙🚀 Solana Dev Backtest AI process complete! 🚀✨")
────────────────────────────

Notes:
• All indicator calculations are wrapped with self.I() and use TA‑Lib (e.g. talib.RSI, talib.MIN, talib.MAX and talib.SMA).
• Data cleaning ensures that CSV columns (open, high, low, close, volume) are converted into the required proper-case names.
• Position sizing is computed based on a percentage of equity and is rounded to an integer.
• Plenty of debug prints with Solana Dev emojis are added to help trace every step of the backtest.
• After running the initial backtest, the script runs an optimization for key parameters 
  and saves both performance charts to the specified charts directory.
  
Happy backtesting! 🌙🚀✨