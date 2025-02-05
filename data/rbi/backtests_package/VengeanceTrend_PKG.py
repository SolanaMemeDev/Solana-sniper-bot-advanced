import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np

# Clean and prepare the data
def prepare_data(filepath):
    data = pd.read_csv(filepath)
    # Clean column names
    data.columns = data.columns.str.strip().str.lower()
    # Drop unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    # Map columns to required format
    data = data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    # Ensure datetime format
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    return data

# Strategy Class
class VengeanceTrend(Strategy):
    # Parameters for optimization
    atr_period = 14  # ATR period for trailing stop
    risk_per_trade = 0.02  # Risk 2% of capital per trade
    trailing_stop_multiplier = 2.0  # Multiplier for ATR-based trailing stop

    def init(self):
        # Calculate ATR for trailing stop
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        print("🌙 Initialized VengeanceTrend Strategy with ATR-based trailing stops! 🚀")

    def next(self):
        # Skip if ATR is not calculated yet
        if len(self.atr) < self.atr_period:
            return

        # Current ATR value
        current_atr = self.atr[-1]

        # Calculate position size based on risk
        risk_amount = self.equity * self.risk_per_trade
        position_size = risk_amount / current_atr

        # Entry logic: Buy on pullback in an uptrend
        if not self.position:
            if self.data.Close[-1] > self.data.Close[-2] and self.data.Close[-2] > self.data.Close[-3]:  # Uptrend
                print("🌙 Detected Uptrend! Looking for a pullback entry... ✨")
                if self.data.Close[-1] < self.data.Close[-2]:  # Pullback
                    self.buy(size=position_size, sl=self.data.Close[-1] - self.trailing_stop_multiplier * current_atr)
                    print(f"🚀 Entered Long at {self.data.Close[-1]} with trailing stop! 🌙")

        # Trailing stop logic
        if self.position:
            if self.position.is_long:
                # Update trailing stop for long positions
                new_sl = self.data.Close[-1] - self.trailing_stop_multiplier * current_atr
                if new_sl > self.position.sl:
                    self.position.sl = new_sl
                    print(f"🌙 Updated Trailing Stop for Long Position to {new_sl} 🚀")

# Load and prepare data
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = prepare_data(data_path)

# Run initial backtest
bt = Backtest(data, VengeanceTrend, cash=1_000_000, commission=0.002)
stats = bt.run()
print("🌙 Initial Backtest Results: 🌙")
print(stats)
print(stats._strategy)

# Plot initial performance
bt.plot()

# Optimize parameters
optimization_results = bt.optimize(
    atr_period=range(10, 20, 2),
    trailing_stop_multiplier=[1.5, 2.0, 2.5],
    risk_per_trade=[0.01, 0.02, 0.03],
    maximize='Return [%]'
)
print("🌙 Optimization Results: 🌙")
print(optimization_results)

# Run backtest with optimized parameters
optimized_stats = bt.run(**optimization_results._params)
print("🌙 Optimized Backtest Results: 🌙")
print(optimized_stats)
print(optimized_stats._strategy)

# Plot optimized performance
bt.plot()