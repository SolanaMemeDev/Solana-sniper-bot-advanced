Here's the backtesting.py implementation for the Structural Demand Reversal strategy:

```python
import os
import pandas as pd
import talib
from datetime import datetime
from typing import Tuple
from backtrader import Cerebro, Strategy, TimeFrame, num2date

# Ensure proper data handling
def preprocess_data(data: pd.DataFrame) -> pd.DataFrame:
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    
    # Ensure required columns are present
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in data.columns:
            raise ValueError(f"Missing required column: {col}")
    
    return data

class StructuralDemandReversal(Strategy):
    params = (
        ('rr_ratio', 2.5),
        ('risk_pct', 1),
    )

    def __init__(self):
        self.trend = None
        self.demand_zones = []
        self.supply_zones = []

    def prenext(self):
        self.trend = self.determine_trend()
        self.identify_demand_supply_zones()

    def next(self):
        if self.trend == 'uptrend':
            self.handle_uptrend()
        elif self.trend == 'downtrend':
            self.handle_downtrend()

    def handle_uptrend(self):
        for zone in self.demand_zones:
            if self.data.low[-1] > zone[0] and self.data.high[-1] < zone[1]:
                self.buy_signal(zone)
                break

    def handle_downtrend(self):
        for zone in self.supply_zones:
            if self.data.high[-1] < zone[1] and self.data.low[-1] > zone[0]:
                self.sell_signal(zone)
                break

    def buy_signal(self, demand_zone: Tuple[float, float]):
        size = self.get_position_size(demand_zone[0], demand_zone[1])
        stop_loss = demand_zone[0] - 0.01
        take_profit = self.find_swing_high(demand_zone[0], demand_zone[1])
        self.buy(size=size, exectype=self.OrderTypes.StopLimit, price=demand_zone[0], valid=stop_loss)
        print(f"🌙 Buying at demand zone: {demand_zone} | Stop Loss: {stop_loss} | Take Profit: {take_profit} | Size: {size:.2f} 💰")

    def sell_signal(self, supply_zone: Tuple[float, float]):
        size = self.get_position_size(supply_zone[0], supply_zone[1])
        stop_loss = supply_zone[1] + 0.01
        take_profit = self.find_swing_low(supply_zone[0], supply_zone[1])
        self.sell(size=size, exectype=self.OrderTypes.StopLimit, price=supply_zone[1], valid=stop_loss)
        print(f"🌙 Selling at supply zone: {supply_zone} | Stop Loss: {stop_loss} | Take Profit: {take_profit} | Size: {size:.2f} 💰")

    def get_position_size(self, entry_price: float, stop_loss: float) -> float:
        risk_per_trade = self.broker.cash * self.params.risk_pct / 100
        atr = self.I(talib.ATR, self.data.close, timeperiod=14)[-1]
        position_size = risk_per_trade / abs(entry_price - stop_loss)
        return position_size

    def find_swing_high(self, demand_low: float, demand_high: float) -> float:
        swing_high = self.I(talib.MAX, self.data.high, timeperiod=20)
        for i in