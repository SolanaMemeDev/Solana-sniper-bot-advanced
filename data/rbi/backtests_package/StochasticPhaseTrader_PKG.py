Here's the fixed code without any usage of `backtesting.lib`:

--------------------------------------------------
#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
import talib

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
               