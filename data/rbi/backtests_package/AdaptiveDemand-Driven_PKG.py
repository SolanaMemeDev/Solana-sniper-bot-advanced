Here's the fixed code with the proper indicator package replacements:

```python
import os
import talib
import pandas as pd
import matplotlib.pyplot as plt
import backtrader as bt
from backtrader.indicators import SMA, MACD
from backtrader.strategies import Strategy
from backtrader.analyzers import SharpeRatio, TradeAnalyzer
from backtrader.feeds import PandasData

class AdaptiveDemandDrivenStrategy(Strategy):
    params = (
        ('rsi_period', 14),
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
        ('risk_reward_ratio', 2.5),
    )

    def __init__(self):
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.params.rsi_period)
        self.macd, self.signal, self.hist = self.I(talib.MACD, self.data.Close, fastperiod=self.params.macd_fast, slowperiod=self.params.macd_slow, signalperiod=self.params.macd_signal)
        self.sma_20 = self.I(talib.SMA, self.data.Close, timeperiod=20)
        self.sma_50 = self.I(talib.SMA, self.data.Close, timeperiod=50)

        self.trend_direction = None
        self.demand_zone_low = None
        self.demand_zone_high = None
        self.supply_zone_low = None
        self.supply_zone_high = None

    def next(self):
        if not self.position:
            self.identify_trend_direction()
            self.identify_demand_supply_zones()

            if self.trend_direction == 'uptrend':
                self.check_long_entry()
            elif self.trend_direction == 'downtrend':
                self.check_short_entry()

        else:
            self.manage_open_position()

    def identify_trend_direction(self):
        if self.data.Close[-2] < self.data.Close[-1] and self.data.Close[-3] < self.data.Close[-2]:
            self.trend_direction = 'uptrend'
        elif self.data.Close[-2] > self.data.Close[-1] and self.data.Close[-3] > self.data.Close[-2]:
            self.trend_direction = 'downtrend'
        else:
            self.trend_direction = None

    def identify_demand_supply_zones(self):
        if self.trend_direction == 'uptrend':
            self.identify_demand_zones()
        elif self.trend_direction == 'downtrend':
            self.identify_supply_zones()

    def identify_demand_zones(self):
        for i in range(1, len(self.data)):
            if self.data.Low[i] > self.data.Low[i-1] and self.data.High[i] > self.data.High[i-1]:
                self.demand_zone_low = self.data.Low[i-1]
                self.demand_zone_high = self.data.High[i-1]
                break
            else:
                self.demand_zone_low = None
                self.demand_zone_high = None

    def identify_supply_zones(self):
        for i in range(1, len(self.data)):
            if self.data.High[i] < self.data.High[i-1] and self.data.Low[i] < self.data.Low[i-1]:
                self.supply_zone_low = self.data.Low[i-1]
                self.supply_zone_high = self.data.High[i-1]
                break
            else:
                self.supply_zone_low = None
                self.supply_zone_high = None

    def check_long_entry(self):
        if (
            self.rsi[-1] < 50
            and self.macd[-1] > self.signal[-1]
            an