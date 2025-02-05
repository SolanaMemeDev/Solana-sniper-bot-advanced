Here's the fixed code with proper Solana Dev themed debug prints, following all the guidelines:

```python
#!/usr/bin/env python3
import os
import pandas as pd
import talib
from backtesting import Backtest
from backtesting.strategies import (
    StopLossMixin,
    TakeProfitMixin,
    CapitalStrategy,
)

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

class StochasticPhaseFilter(StopLossMixin, TakeProfitMixin, CapitalStrategy):
    # Define strategy parameters (optimization ranges are integers so percentages are in whole numbers)
    overbought = 80  # overbought threshold (to trigger SELL signals)
    oversold = 20  # oversold threshold (to trigger BUY signals)
    stop_loss_pct = 1  # stop loss as a percentage of price (1% by default)
    reward_risk = 2  # reward-to-risk ratio (default: 2)
    risk_pct = 1  # risk 1% of equity per trade

    def __init__(self):
        self.rsi = None
        self.lowest_rsi = None
        self.highest_rsi = None
        self.stoch_rsi = None
        self.stoch_rsi_smoothed = None

    def informative_pairs(self):
        return []

    def populate_indicators(self, dataframe):
        self.rsi = self.I(talib.RSI, dataframe.Close, timeperiod=14)
        self.lowest_rsi = self.I(talib.MIN, self.rsi, timeperiod=14)
        self.highest_rsi = self.I(talib.MAX, self.rsi, timeperiod=1