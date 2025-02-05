import pandas as pd
import talib
from backtesting import Backtest, Strategy

# Clean and prepare the data
data = pd.read_csv("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv")

# Clean column names and drop unnamed columns
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Ensure proper column mapping
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# Convert datetime column to proper format
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

class EMAVolumeSync(Strategy):
    # Strategy parameters
    ema_period = 20
    volume_ma_period = 20
    risk_per_trade = 0.01  # Risk 1% of capital per trade
    risk_reward_ratio = 2  # 2:1 risk-reward ratio

    def init(self):
        # Calculate EMAs
        self.green_ema = self.I(talib.EMA, self.data.High, timeperiod=self.ema_period)
        self.red_ema = self.I(talib.EMA, self.data.Low, timeperiod=self.ema_period)

        # Calculate Volume Moving Average
        self.volume_ma = self.I(talib.SMA, self.data.Volume, timeperiod=self.volume_ma_period)

        # Debug prints
        print("🌙 EMAVolumeSync Strategy Initialized! ✨")
        print(f"📊 Green EMA (High): {self.ema_period} periods")
        print(f"📊 Red EMA (Low): {self.ema_period} periods")
        print(f"📊 Volume MA: {self.volume_ma_period} periods")
        print(f"⚠️ Risk per trade: {self.risk_per_trade * 100}%")
        print(f"🎯 Risk-Reward Ratio: {self.risk_reward_ratio}:1")

    def next(self):
        # Skip if indicators are not ready
        if len(self.data) < self.ema_period or len(self.data) < self.volume_ma_period:
            return

        # Current price and volume
        current_close = self.data.Close[-1]
        current_volume = self.data.Volume[-1]

        # Trend direction
        is_uptrend = current_close > self.green_ema[-1] and current_close > self.red_ema[-1]
        is_downtrend = current_close < self.green_ema[-1] and current_close < self.red_ema[-1]

        # Volume confirmation
        volume_confirmation = current_volume > self.volume_ma[-1]

        # Entry logic for long trades
        if is_uptrend and volume_confirmation:
            if not self.position:
                # Calculate position size based on risk
                stop_loss = self.red_ema[-1]  # Use Red EMA as stop loss
                risk_amount = self.risk_per_trade * self.equity
                position_size = risk_amount / (current_close - stop_loss)

                # Enter long trade
                self.buy(size=position_size, sl=stop_loss, tp=current_close + (current_close - stop_loss) * self.risk_reward_ratio)
                print(f"🚀 Long Entry at {current_close} | SL: {stop_loss} | TP: {current_close + (current_close - stop_loss) * self.risk_reward_ratio}")

        # Entry logic for short trades
        elif is_downtrend and volume_confirmation:
            if not self.position:
                # Calculate position size based on risk
                stop_loss = self.green_ema[-1]  # Use Green EMA as stop loss
                risk_amount = self.risk_per_trade * self.equity
                position_size = risk_amount / (stop_loss - current_close)

                # Enter short trade
                self.sell(size=position_size, sl=stop_loss, tp=current_close - (stop_loss - current_close) * self.risk_reward_ratio)
                print(f"📉 Short Entry at {current_close} | SL: {stop_loss} | TP: {current_close - (stop_loss - current_close) * self.risk_reward_ratio}")

        # Exit logic
        if self.position:
            # Bullish crossover detection (replacing crossunder)
            if is_uptrend and (self.data.Close[-2] > self.red_ema[-2] and self.data.Close[-1] < self.red_ema[-1]):
                self.position.close()
                print(f"🌙 Exit Long at {current_close} | Trend Reversal Detected ✨")
            # Bearish crossover detection (replacing crossover)
            elif is_downtrend and (self.data.Close[-2] < self.green_ema[-2] and self.data.Close[-1] > self.green_ema[-1]):
                self.position.close()
                print(f"🌙 Exit Short at {current_close} | Trend Reversal Detected ✨")

# Initialize backtest
bt = Backtest(data, EMAVolumeSync, cash=1_000_000, commission=0.002)

# Run initial backtest
stats = bt.run()
print(stats)
print(stats._strategy)

# Show initial performance plot
bt.plot()

# Optimize parameters
optimization_results = bt.optimize(
    ema_period=range(15, 25, 1),
    volume_ma_period=range(15, 25, 1),
    risk_reward_ratio=[2, 3],
    maximize='Return [%]'
)

# Print optimized results
print("🎉 Optimized Results 🎉")
print(optimization_results)

# Show optimized performance plot
bt.plot()