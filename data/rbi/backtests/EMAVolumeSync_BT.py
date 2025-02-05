import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

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

def crossunder(series1, series2):
    """Return True if series1 crosses under series2"""
    return crossover(series2, series1)

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
                stop_loss = min(self.red_ema[-1], current_close * 0.98)  # At least 2% below entry
                risk_amount = self.risk_per_trade * self.equity
                position_size = risk_amount / abs(current_close - stop_loss)
                position_size = max(1, round(position_size / current_close))  # Convert to whole units

                # For longs, take profit must be above entry price
                take_profit = current_close * (1 + (self.risk_reward_ratio * 0.02))  # 2% * RR above entry

                # Enter long trade
                self.buy(size=position_size, sl=stop_loss, tp=take_profit)
                print(f"🚀 Long Entry at {current_close} | SL: {stop_loss} | TP: {take_profit}")

        # Entry logic for short trades
        elif is_downtrend and volume_confirmation:
            if not self.position:
                # For shorts, stop loss must be above entry price
                stop_loss = max(self.green_ema[-1], current_close * 1.02)  # At least 2% above entry
                risk_amount = self.risk_per_trade * self.equity
                position_size = risk_amount / abs(stop_loss - current_close)
                position_size = max(1, round(position_size / current_close))  # Convert to whole units

                # For shorts, take profit must be below entry price
                take_profit = current_close * (1 - (self.risk_reward_ratio * 0.02))  # 2% * RR below entry

                # Enter short trade
                self.sell(size=position_size, sl=stop_loss, tp=take_profit)
                print(f"📉 Short Entry at {current_close} | SL: {stop_loss} | TP: {take_profit}")

        # Exit logic
        if self.position:
            if self.position.is_long and crossunder(self.data.Close, self.red_ema):
                self.position.close()
                print(f"🌙 Exit Long at {current_close} | Trend Reversal Detected ✨")
            elif self.position.is_short and crossover(self.data.Close, self.green_ema):
                self.position.close()
                print(f"🌙 Exit Short at {current_close} | Trend Reversal Detected ✨")

if __name__ == "__main__":
    # Initialize backtest
    bt = Backtest(data, EMAVolumeSync, cash=1_000_000, commission=0.002)

    # Run initial backtest
    print("\n🌙 Running initial backtest...")
    stats = bt.run()
    print("\n📊 Backtest Stats:")
    print(stats)

    # # Show initial performance plot
    # bt.plot()

    # # Optimize parameters
    # print("\n✨ Running optimization...")
    # optimization_results = bt.optimize(
    #     ema_period=range(15, 25, 1),
    #     volume_ma_period=range(15, 25, 1),
    #     risk_reward_ratio=[2, 3],
    #     maximize='Return [%]'
    # )

    # # Print optimized results
    # print("\n🎉 Optimized Results 🎉")
    # print(optimization_results)

    # # Show optimized performance plot
    # bt.plot()