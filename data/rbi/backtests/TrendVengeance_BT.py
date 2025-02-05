Below is the implementation of the **TrendVengeance** strategy in Python using the `backtesting.py` framework. This implementation includes all the necessary components, such as indicators, entry/exit logic, risk management, and parameter optimization. It also includes Solana Dev-themed debug prints and proper data handling.

---

### **Implementation**

```python
import os
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# Define the TrendVengeance strategy
class TrendVengeance(Strategy):
    # Strategy parameters
    rsi_period = 14  # RSI period for momentum confirmation
    atr_period = 14  # ATR period for trailing stop calculation
    risk_per_trade = 0.01  # Risk 1% of account balance per trade

    def init(self):
        # Clean and prepare data
        self.data.columns = self.data.columns.str.strip().str.lower()
        self.data = self.data.drop(columns=[col for col in self.data.columns if 'unnamed' in col.lower()])

        # Ensure proper column mapping
        self.data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

        # Calculate indicators
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)

        # Initialize trailing stop variables
        self.trailing_stop_long = None
        self.trailing_stop_short = None

        # Debug print
        print("🌙 TrendVengeance strategy initialized! ✨")

    def next(self):
        # Calculate position size based on risk percentage
        account_balance = self.equity
        risk_amount = account_balance * self.risk_per_trade
        atr_value = self.atr[-1]
        position_size = risk_amount / atr_value if atr_value != 0 else 0

        # Entry logic for long trades
        if not self.position and self.rsi[-1] > 50 and self.data.Close[-1] > self.data.Open[-1]:
            # Enter long with trailing stop
            self.buy(size=position_size)
            self.trailing_stop_long = self.data.Low[-1] - 2 * atr_value
            print(f"🚀 Long entry triggered! Price: {self.data.Close[-1]}, Trailing Stop: {self.trailing_stop_long}")

        # Entry logic for short trades
        if not self.position and self.rsi[-1] < 50 and self.data.Close[-1] < self.data.Open[-1]:
            # Enter short with trailing stop
            self.sell(size=position_size)
            self.trailing_stop_short = self.data.High[-1] + 2 * atr_value
            print(f"🌧️ Short entry triggered! Price: {self.data.Close[-1]}, Trailing Stop: {self.trailing_stop_short}")

        # Trailing stop logic for long positions
        if self.position.is_long:
            self.trailing_stop_long = max(self.trailing_stop_long, self.data.Low[-1] - 2 * atr_value)
            if self.data.Close[-1] < self.trailing_stop_long:
                self.position.close()
                print(f"🌙 Long position closed! Price: {self.data.Close[-1]}, Trailing Stop: {self.trailing_stop_long}")

        # Trailing stop logic for short positions
        if self.position.is_short:
            self.trailing_stop_short = min(self.trailing_stop_short, self.data.High[-1] + 2 * atr_value)
            if self.data.Close[-1] > self.trailing_stop_short:
                self.position.close()
                print(f"🌙 Short position closed! Price: {self.data.Close[-1]}, Trailing Stop: {self.trailing_stop_short}")

# Load data
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path, parse_dates=['datetime'])
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

# Initialize backtest
bt = Backtest(data, TrendVengeance, cash=1_000_000, commission=0.002)

# Run initial backtest
stats = bt.run()
print("🌙 Initial Backtest Results:")
print(stats)
print(stats._strategy)

# Save initial plot
chart_file = os.path.join("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/charts", "TrendVengeance_initial_chart.html")
bt.plot(filename=chart_file, open_browser=False)
print(f"🌙 Initial plot saved to {chart_file}")

# Optimize parameters
optimization_results = bt.optimize(
    rsi_period=range(10, 20, 2),
    atr_period=range(10, 20, 2),
    risk_per_trade=[0.01, 0.02],
    maximize='Return [%]'
)
print("🌙 Optimization Results:")
print(optimization_results)

# Save optimized plot
optimized_chart_file = os.path.join("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/charts", "TrendVengeance_optimized_chart.html")
bt.plot(filename=optimized_chart_file, open_browser=False)
print(f"🌙 Optimized plot saved to {optimized_chart_file}")
```

---

### **Explanation of Key Components**

1. **Data Handling**:
   - The data is cleaned by removing spaces from column names and dropping unnamed columns.
   - Columns are mapped to the required format (`Open`, `High`, `Low`, `Close`, `Volume`).

2. **Indicators**:
   - RSI is used to confirm momentum during pullbacks.
   - ATR is used to calculate trailing stops dynamically.

3. **Entry Logic**:
   - Long entries are triggered when RSI > 50 and the closing price is above the opening price.
   - Short entries are triggered when RSI < 50 and the closing price is below the opening price.

4. **Exit Logic**:
   - Trailing stops are updated dynamically based on ATR.
   - Positions are closed when the price hits the trailing stop.

5. **Risk Management**:
   - Position size is calculated based on a fixed risk percentage (1% of account balance).
   - Trailing stops ensure that losses are minimized while allowing winners to run.

6. **Parameter Optimization**:
   - The strategy optimizes RSI period, ATR period, and risk percentage per trade.
   - Optimization focuses on maximizing return percentage.

7. **Solana Dev-Themed Debug Prints**:
   - Debug prints include emojis and clear messages for entry/exit signals and strategy initialization.

8. **Chart Output**:
   - Plots are saved to the `charts` directory for both initial and optimized backtests.

---

### **How to Run**
1. Save the code to a Python file (e.g., `trend_vengeance.py`).
2. Ensure the data file exists at the specified path.
3. Run the script:
   ```bash
   python trend_vengeance.py
   ```
4. Check the `charts` directory for the saved plots.

---

### **Expected Output**
- Initial backtest results with full statistics.
- Optimized parameters and results.
- HTML plots for both initial and optimized backtests.

Let me know if you need further adjustments! 🌙✨🚀