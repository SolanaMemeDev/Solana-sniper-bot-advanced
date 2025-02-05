Here's the implementation of the Adaptive Stochastic Reversal strategy using the provided data:

```python
import os
import pandas as pd
import talib
from datetime import datetime, timedelta
import backtrader as bt

class AdaptiveStochasticReversal(bt.Strategy):
    params = (
        ('stoch_rsi_period', 14),
        ('stoch_rsi_smoothK', 3),
        ('stoch_rsi_smoothD', 3),
        ('weekly_oversold', 15),
        ('weekly_overbought', 80),
        ('shorter_timeframe_oversold', 20),
        ('shorter_timeframe_overbought', 80),
        ('risk_pct', 0.02),
        ('rr_ratio', 2),
    )

    def __init__(self):
        self.stoch_rsi = self.I(talib.STOCHRSI, self.data.Close, fastk_period=self.params.stoch_rsi_period, fastd_period=self.params.stoch_rsi_smoothK, fastd_matype=talib.MA_Type.SMA)

    def next(self):
        if not self.position:
            # Weekly/Long-term Timeframe
            if self.stoch_rsi[-1] < self.params.weekly_oversold:
                self.buy(size=self.stake)
                print(f"🌙 Bought at: {self.data.Close[0]:.2f} 💫")

            # Shorter Timeframe
            elif self.stoch_rsi[-1] > self.params.shorter_timeframe_overbought:
                self.sell(size=self.stake)
                print(f"✨ Sold at: {self.data.Close[0]:.2f} 🚀")
        else:
            if self.stoch_rsi[-1] > self.params.weekly_overbought:
                self.sell(size=self.stake)
                print(f"✨ Sold at: {self.data.Close[0]:.2f} 🚀")

            # Trailing Stop-Loss
            if self.data.Close[0] < self.data.Close[-1] * (1 - self.params.risk_pct):
                self.sell(size=self.stake)
                print(f"🌙 Stopped out at: {self.data.Close[0]:.2f} 💫")

    def notify_trade(self, trade):
        if trade.justopened:
            print(f"🌙 Opened trade at: {trade.price:.2f} 💫")
        elif trade.isclosed:
            print(f"✨ Closed trade. Total profit/loss: {trade.pnl:.2f} 🚀")

def run_backtest(data_path):
    # Load data
    data = pd.read_csv(data_path)
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

    # Ensure proper column mapping
    data = data.rename(columns={
        'datetime': 'date',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })

    # Create Cerebro engine
    cerebro = bt.Cerebro(stdstats=False)

    # Add the strategy
    cerebro.addstrategy(AdaptiveStochasticReversal)

    # Set the initial cash
    cerebro.broker.setcash(1000000.0)

    # Add the data feed
    data = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data)

    # Run the backtest
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Save the chart