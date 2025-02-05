Sure, here's a backtesting implementation for the Trend-Breakout Reversal strategy:

```python
import os
import pandas as pd
import talib
from backtest_ai import Backtest

class TrendBreakoutReversal:
    def __init__(self, data, capital=1_000_000, risk_pct=0.02, rr_ratio=2, consolidation_range=100, breakout_bars=3):
        self.data = data
        self.capital = capital
        self.risk_pct = risk_pct
        self.rr_ratio = rr_ratio
        self.consolidation_range = consolidation_range
        self.breakout_bars = breakout_bars

    def I(self, indicator, *args, **kwargs):
        """Wrapper for indicator calculations"""
        return indicator(self.data.values, *args, **kwargs)

    def get_market_trend(self):
        """Determine the overall market trend direction"""
        weekly_highs = self.I(talib.MAX, self.data.High, timeperiod=336)  # 1 week
        weekly_lows = self.I(talib.MIN, self.data.Low, timeperiod=336)

        if weekly_highs[-1] > weekly_highs[-2] and weekly_lows[-1] > weekly_lows[-2]:
            return "Uptrend"
        elif weekly_highs[-1] < weekly_highs[-2] and weekly_lows[-1] < weekly_lows[-2]:
            return "Downtrend"
        else:
            return "Sideways"

    def check_consolidation(self):
        """Check if the market is in a consolidation range"""
        daily_high = self.I(talib.MAX, self.data.High, timeperiod=96)  # 4 days
        daily_low = self.I(talib.MIN, self.data.Low, timeperiod=96)

        consolidation_range = daily_high - daily_low
        return consolidation_range[-1] < self.consolidation_range

    def check_breakout(self):
        """Check for a breakout of the consolidation range"""
        current_close = self.data.Close[-1]
        daily_high = self.I(talib.MAX, self.data.High, timeperiod=96)
        daily_low = self.I(talib.MIN, self.data.Low, timeperiod=96)

        if current_close > daily_high[-self.breakout_bars:].max():
            return "Bullish"
        elif current_close < daily_low[-self.breakout_bars:].min():
            return "Bearish"
        else:
            return "No Breakout"

    def get_entry_price(self, signal):
        """Get the entry price based on the breakout signal"""
        if signal == "Bullish":
            return self.data.Open[-1]
        elif signal == "Bearish":
            return self.data.Open[-1]
        else:
            return None

    def get_stop_loss(self, signal):
        """Calculate the stop-loss price"""
        daily_high = self.I(talib.MAX, self.data.High, timeperiod=96)
        daily_low = self.I(talib.MIN, self.data.Low, timeperiod=96)

        if signal == "Bullish":
            return daily_low[-self.breakout_bars:].min()
        elif signal == "Bearish":
            return daily_high[-self.breakout_bars:].max()
        else:
            return None

    def get_take_profit(self, entry_price, stop_loss):
        """Calculate the take-profit price"""
        risk = entry_price - stop_loss
        return entry_price + (risk * self.rr_ratio)

    def should_trade(self):
        """Determine if a trade should be executed"""
        market_trend = self.get_market_trend()
        is_consolidating = self.check_consolidation()
        breakout_signal = self.check_breakout()

        if market_trend in ["Uptrend", "