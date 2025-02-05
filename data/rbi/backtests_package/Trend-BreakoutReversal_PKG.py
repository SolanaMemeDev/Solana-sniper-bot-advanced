Sure, here's the fixed code with proper Solana Dev themed debug prints:

```python
import os
import pandas as pd
import talib
import pandas_ta as pta
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
        print(f"🌙 Calculating indicator: {indicator.__name__}")
        return indicator(self.data.values, *args, **kwargs)

    def get_market_trend(self):
        """Determine the overall market trend direction"""
        print("🌙 Checking market trend...")
        weekly_highs = self.I(talib.MAX, self.data.High, timeperiod=336)  # 1 week
        weekly_lows = self.I(talib.MIN, self.data.Low, timeperiod=336)

        if weekly_highs[-1] > weekly_highs[-2] and weekly_lows[-1] > weekly_lows[-2]:
            print("🌙 Market is in an uptrend")
            return "Uptrend"
        elif weekly_highs[-1] < weekly_highs[-2] and weekly_lows[-1] < weekly_lows[-2]:
            print("🌙 Market is in a downtrend")
            return "Downtrend"
        else:
            print("🌙 Market is in a sideways trend")
            return "Sideways"

    def check_consolidation(self):
        """Check if the market is in a consolidation range"""
        print("🌙 Checking market consolidation...")
        daily_high = self.I(talib.MAX, self.data.High, timeperiod=96)  # 4 days
        daily_low = self.I(talib.MIN, self.data.Low, timeperiod=96)

        consolidation_range = daily_high - daily_low
        is_consolidating = consolidation_range[-1] < self.consolidation_range
        print(f"🌙 Market is {'consolidating' if is_consolidating else 'not consolidating'}")
        return is_consolidating

    def check_breakout(self):
        """Check for a breakout of the consolidation range"""
        print("🌙 Checking for market breakout...")
        current_close = self.data.Close[-1]
        daily_high = self.I(talib.MAX, self.data.High, timeperiod=96)
        daily_low = self.I(talib.MIN, self.data.Low, timeperiod=96)

        if current_close > daily_high[-self.breakout_bars:].max():
            print("🌙 Bullish breakout detected")
            return "Bullish"
        elif current_close < daily_low[-self.breakout_bars:].min():
            print("🌙 Bearish breakout detected")
            return "Bearish"
        else:
            print("🌙 No breakout detected")
            return "No Breakout"

    def get_entry_price(self, signal):
        """Get the entry price based on the breakout signal"""
        print("🌙 Determining entry price...")
        if signal == "Bullish":
            return self.data.Open[-1]
        elif signal == "Bearish":
            return self.data.Open[-1]
        else:
            return None

    def get_stop_loss(self, signal):
        """Calculate the stop-loss price"""
        print("🌙 Calculating stop-loss price...")
        daily_high = self.I(talib.MAX, self.data.High, timeperiod=96)