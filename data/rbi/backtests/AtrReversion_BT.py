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
        prev_open = self.data.Open[-2]
        prev_high = self.data.High[-2]
        prev_low = self.data.Low[-2]
        prev_close = self.data.Close[-2]
        prev_keltner_upper = self.keltner_upper[-2]
        prev_keltner_lower = self.keltner_lower[-2]

        # Setup our account sizing: full account_size is defined externally as 1,000,000.
        # For these trades we use trade_fraction (half size).
        account_size = 1000000
        risk_amount = account_size * self.risk_percent * self.trade_fraction  # e.g., 1% risk half-sized
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #  A) Potential SHORT Trade Entry (mean reversion from overextended high)
        # Condition: prior candle closed above the upper Keltner channel and current candle is a bearish reversal candle.
        # We then place a sell stop order below the reversal candle.
        if prev_close > prev_keltner_upper and C < O:
            entry_price = L  # we look to enter at the current low (or slightly below reversal candle low)
            # For short, stop loss is set just above the reversal candle's high.
            stop_loss = prev_high * 1.001  # a tiny buffer – Solana Dev style!
            risk_per_unit = stop_loss - entry_price
            print(f"🌙🔥 [SIGNAL] SHORT candidate detected! Prev Close {prev_close:.2f} > Prev KC Upper {prev_keltner_upper:.2f} and current bearish candle (O {O:.2f} > C {C:.2f})")
            if risk_per_unit > 0:
                position_size = int(round(risk_amount / risk_per_unit))
                if position_size > 0:
                    print(f"🌙💰 [ORDER] Enter SHORT: entry={entry_price:.2f}, stop_loss={stop_loss:.2f}, risk_per_unit={risk_per_unit:.2f}, size={position_size}")
                    # Place a short order with a protective stop loss.
                    self.sell(size=position_size, sl=stop_loss)
                else:
                    print("🌙⚠️ [SKIP] Calculated position size is 0. Check risk parameters!")
            else:
                print("🌙⚠️ [SKIP] Risk per unit <= 0 for short; not entering trade.")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #  B) Potential LONG Trade Entry (mean reversion from extended low)
        # Condition: prior candle closed below the lower Keltner channel and current candle is a bullish reversal candle.
        # We then place a buy stop order above the reversal candle.
        elif prev_close < prev_keltner_lower and C > O:
            entry_price = H  # aiming to enter at the current high (or slightly above the reversal candle high)
            # For long, stop loss is set just below the reversal candle's low.
            stop_loss = prev_low * 0.999  # a tiny buffer – Solana Dev style!
            risk_per_unit = entry_price - stop_loss
            print(f"🌙🔥 [SIGNAL] LONG candidate detected! Prev Close {prev_close:.2f} < Prev KC Lower {prev_keltner_lower:.2f} and current bullish candle (C {C:.2f} > O {O:.2f})")
            if risk_per_unit > 0:
                position_size = int(round(risk_amount / risk_per_unit))
                if position_size > 0:
                    print(f"🌙💰 [ORDER] Enter LONG: entry={entry_price:.2f}, stop_loss={stop_loss:.2f}, risk_per_unit={risk_per_unit:.2f}, size={position_size}")
                    self.buy(size=position_size, sl=stop_loss)
                else:
                    print("🌙⚠️ [SKIP] Calculated position size is 0. Check risk parameters!")
            else:
                print("🌙⚠️ [SKIP] Risk per unit <= 0 for long; not entering trade.")


# 3. Load and prepare the data
def load_data(filepath):
    # Read CSV file
    print("🌙📥 [LOAD] Loading CSV data from:", filepath)
    data = pd.read_csv(filepath, parse_dates=['datetime'])
    # Clean column names: remove spaces and set to lowercase
    data.columns = data.columns.str.strip().str.lower()

    # Drop any unnamed columns:
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()], errors='ignore')

    # Map to required column names with proper case:
    # Expected: 'Open', 'High', 'Low', 'Close', 'Volume'
    rename_dict = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
    data = data.rename(columns=rename_dict)

    # Set datetime as index (if not already)
    if 'datetime' in data.columns:
        data.set_index('datetime', inplace=True)
    print("🌙✅ [LOAD] Data loaded and formatted. Columns: ", list(data.columns))
    return data

# 4. Main backtest execution
if __name__ == '__main__':
    # Path to the data file
    data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
    df = load_data(data_path)

    # Ensure the data is sorted by datetime
    df.sort_index(inplace=True)

    # 5. Backtest instance with size = 1,000,000
    bt = Backtest(
        df, 
        AtrReversion, 
        cash=1000000, 
        commission=0.0,  # adjust commission if needed
        exclusive_orders=True
    )
    print("🌙🚀 [BACKTEST] Starting the backtest of AtrReversion Strategy...")

    # 6. Run the backtest and print full stats (no plotting)
    stats = bt.run()
    print("\n🌙📊 [STATS] Full Backtest Stats:")
    print(stats)
    print("\n🌙🔍 [STRATEGY DETAILS] Strategy Instance:")
    print(stats._strategy)

    # No charts per instructions!
    print("🌙👍 [DONE] Backtest complete! Keep reaching for the moon! 🚀✨")
    
# End of file
