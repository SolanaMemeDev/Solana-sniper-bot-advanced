Below is the complete fixed code with Solana Dev themed debug prints. No strategy logic was changed; only syntax, scoping, and sizing issues (plus indicator/stop level usage) were fixed. Enjoy, and keep on mooning! 🌙✨

--------------------------------------------------
#!/usr/bin/env python3
"""
Solana Dev's Backtest AI 🌙
Strategy: AtrReversion
This strategy uses ATR and Keltner Channels to spot overextended markets and then enters mean‐reversion trades following a 2B price pattern.
Have fun & moon on! 🚀✨
"""

# 1. All necessary imports
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

# 2. Strategy class with indicators, entry/exit logic, and risk management

class AtrReversion(Strategy):
    # Configurable parameters (DON'T CHANGE LOGIC or risk settings)
    atr_period = 14
    ema_period = 20
    keltner_mult = 2.0
    risk_percent = 0.01      # 1% risk per trade (of full equity)
    trade_fraction = 0.5     # use half of our normal size for these trades (fraction of equity)
    
    def init(self):
        # Use self.I() wrapper for indicator calculations
        # Calculate ATR for risk/extension measure
        self.atr = self.I(talib.ATR,
                            self.data.High,
                            self.data.Low,
                            self.data.Close,
                            self.atr_period)
        # Calculate EMA as the midline for Keltner Channels
        self.ema = self.I(talib.EMA, self.data.Close, self.ema_period)
        # Create Keltner Channels from EMA and ATR.
        # Upper Channel = EMA + keltner_mult * ATR
        # Lower Channel = EMA - keltner_mult * ATR
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
            # Exit logic: exit when price reverts back near the EMA midline.
            if self.position.is_short and C < self.ema[-1]:
                print("🌙💥 [EXIT] Short position closed! Price has reverted near the EMA midline.")
                self.position.close()
            elif self.position.is_long and C > self.ema[-1]:
                print("🌙💥 [EXIT] Long position closed! Price has reverted near the EMA midline.")
                self.position.close()
            return  # Do not open a new trade while in a position

        # ENTRY LOGIC for potential mean-reversion trades using the previous candle as the reversal candle.
        # Grab previous candle prices (index -2)
        prev_open = self.data.Open[-2]
        prev_high = self.data.High[-2]
        prev_low = self.data.Low[-2]
        prev_close = self.data.Close[-2]

        # Using Keltner channel indicator values from previous bar (index -2)
        prev_keltner_upper = self.keltner_upper[-2]
        prev_keltner_lower = self.keltner_lower[-2]
        prev_ema = self.ema[-2]

        # For Short trade entry:
        #   Condition: previous candle closed above the upper Keltner channel (overextension)
        #   and current candle price shows signs of reversal (i.e. current close below EMA).
        if prev_close > prev_keltner_upper and C < self.ema[-1]:
            # Calculate order size: trade_fraction is less than 1 so we treat it as a fraction of equity.
            order_size = self.trade_fraction  # using fractional sizing
            print("🌙 [ENTRY] Short trade signal detected. Prev close:", prev_close,
                  " > Prev Upper:", prev_keltner_upper, " | Current C:", C)
            # For protection, set stop loss at the high of the reversal candle (price level)
            stop_level = prev_high
            # Place a sell (short) order. (Using size as fraction of equity)
            self.sell(size=order_size, sl=stop_level)
            
        # For Long trade entry:
        #   Condition: previous candle closed below the lower Keltner channel (overextended low)
        #   and current candle price shows reversal (i.e. current close above EMA).
        elif prev_close < prev_keltner_lower and C > self.ema[-1]:
            order_size = self.trade_fraction  # fractional sizing
            print("🌙 [ENTRY] Long trade signal detected. Prev close:", prev_close,
                  " < Prev Lower:", prev_keltner_lower, " | Current C:", C)
            # Stop loss at the low of the reversal candle (price level)
            stop_level = prev_low
            # Place a buy (long) order.
            self.buy(size=order_size, sl=stop_level)

# Example usage:
# Assuming you have a DataFrame "data" with columns: Open, High, Low, Close and a DateTime index:
# Uncomment below lines to run your backtest with a CSV or DataFrame input.
#
# if __name__ == '__main__':
#     data = pd.read_csv('your_data.csv', parse_dates=True, index_col='Date')
#     bt = Backtest(data, AtrReversion, cash=100000, commission=.0005)
#     stats = bt.run()
#     print("🌙 [STATS] Backtest results:")
#     print(stats)
#     bt.plot()

--------------------------------------------------

Happy backtesting and moon on! 🌙🚀✨