Sure, here's the backtesting.py implementation for the Trend-Breakout Momentum strategy:

```python
import os
import pandas as pd
import talib
import numpy as np
from collections import deque
from datetime import datetime, timedelta

class TrendBreakoutMomentumStrategy:
    def __init__(self, data, risk_pct=0.02, rr_ratio=2, fib_level_1=range(30, 40, 2), fib_level_2=range(50, 60, 2)):
        self.data = data
        self.risk_pct = risk_pct
        self.rr_ratio = rr_ratio
        self.fib_level_1 = fib_level_1
        self.fib_level_2 = fib_level_2
        self.signals = pd.DataFrame(index=self.data.index)
        self.equity = pd.Series(index=self.data.index)
        self.equity.iloc[0] = 1_000_000  # Initial account balance

    def I(self, indicator, *args, **kwargs):
        """Wrapper for indicator calculations using TA-Lib"""
        return indicator(self.data.Close.values, *args, **kwargs)

    def get_trend_direction(self):
        """Determine the overall trend direction using weekly and daily timeframes"""
        weekly_sma = self.I(talib.SMA, self.data.Close, timeperiod=52)
        daily_sma = self.I(talib.SMA, self.data.Close, timeperiod=20)
        trend_direction = 1 if daily_sma > weekly_sma else -1
        return trend_direction

    def find_consolidation(self, timeframe='4H'):
        """Identify sideways/consolidation phases on the 4-hour timeframe"""
        if timeframe == '4H':
            data = self.data.resample('4H').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
        else:
            raise ValueError("Invalid timeframe. Only '4H' is supported.")

        atr = self.I(talib.ATR, timeperiod=14)
        consolidation = (data.High - data.Low) < atr.reindex(data.index)
        return consolidation

    def find_breakout(self, timeframe='1H'):
        """Identify breakouts on the 1-hour and 15-minute timeframes"""
        if timeframe == '1H':
            data = self.data.resample('1H').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
        elif timeframe == '15T':
            data = self.data.resample('15T').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
        else:
            raise ValueError("Invalid timeframe. Only '1H' and '15T' are supported.")

        fib_level_1 = self.fib_level_1
        fib_level_2 = self.fib_level_2
        trend_direction = self.get_trend_direction()

        breakout = pd.Series(index=data.index, dtype=int)
        breakout[:] = 0

        for i in range(len(data)):
            if i > 0:
                if trend_direction == 1:
                    if data.Low[i] > data.Low[i-1] * (1 + fib_level_1/100):
                        breakout[i] = 1
                    elif data.High[i] > data.High[i-1] * (1 + fib_level_2/100):
                        breakout[i] = 1
                else:
                    if data.High[i] < data.High[i-1] * (1 - fib_level_1/100):
                        break