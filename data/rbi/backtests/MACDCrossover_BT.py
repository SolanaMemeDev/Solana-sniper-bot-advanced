#!/usr/bin/env python
"""
MACD Crossover Strategy 🌙✨
- Uses MACD crossovers to identify potential trend changes
- Implements proper risk management with fixed risk per trade
- Includes Solana Dev's signature easter eggs and emojis
"""

import os
import pandas as pd
import pandas_ta as ta
from backtesting import Strategy, Backtest

# Directory setup
BASE_DIR = "src/data/rbi"
DATA_PATH = os.path.join(BASE_DIR, "BTC-USD-15m.csv")
STATS_DIR = os.path.join(BASE_DIR, "backtests/stats")
CHARTS_DIR = os.path.join(BASE_DIR, "backtests/charts")

def load_and_clean_data():
    """Load and clean the OHLCV data"""
    print("🌙 Solana Dev is loading the data...")
    
    # Load the data
    df = pd.read_csv(DATA_PATH)
    
    # Clean column names
    df.columns = df.columns.str.strip().str.lower()
    df = df.loc[:, ~df.columns.str.contains('^unnamed')]
    
    # Rename to match backtesting.py requirements
    column_mapping = {
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }
    df = df.rename(columns=column_mapping)
    
    print("✨ Data loaded successfully!")
    print(f"🔍 Columns: {list(df.columns)}")
    
    return df

class MACDCrossover(Strategy):
    """MACD Crossover strategy with Solana Dev's special touch ✨"""
    
    # Define parameters
    fast_period = 12
    slow_period = 26
    signal_period = 9
    atr_period = 14
    risk_per_trade = 0.01  # 1% risk per trade
    
    def init(self):
        """Initialize the strategy with MACD and ATR indicators"""
        print("🌙 Solana Dev is calculating indicators...")
        
        # Calculate MACD
        macd = self.I(ta.macd, self.data.Close, 
                     fast=self.fast_period, 
                     slow=self.slow_period, 
                     signal=self.signal_period)
        self.macd_line = macd['MACD_12_26_9']
        self.signal_line = macd['MACDs_12_26_9']
        self.macd_hist = macd['MACDh_12_26_9']
        
        # Calculate ATR for position sizing
        self.atr = self.I(ta.atr, self.data.High, self.data.Low, 
                         self.data.Close, length=self.atr_period)
        
        print("✨ Indicators calculated successfully!")
    
    def next(self):
        """Define the trading logic for each candle"""
        
        # Skip if not enough data
        if not len(self.macd_line) > 1:
            return
        
        # Get current price and ATR
        price = self.data.Close[-1]
        atr = self.atr[-1]
        
        # Calculate account value and risk amount
        account_value = self.equity
        risk_amount = account_value * self.risk_per_trade
        
        # Check for MACD crossovers
        macd_current = self.macd_line[-1]
        macd_prev = self.macd_line[-2]
        signal_current = self.signal_line[-1]
        signal_prev = self.signal_line[-2]
        
        # Long Entry: MACD crosses above Signal
        if (macd_prev <= signal_prev and 
            macd_current > signal_current and 
            not self.position):
            
            # Set stop loss and take profit
            stop_loss = price - atr
            take_profit = price + (1.5 * atr)  # 1:1.5 risk/reward
            
            # Calculate position size
            risk_per_unit = price - stop_loss
            pos_size = int(risk_amount / risk_per_unit) if risk_per_unit > 0 else 0
            
            if pos_size > 0 and stop_loss < price < take_profit:
                print(f"🌙🚀 [LONG ENTRY] Solana Dev spotted a Bullish MACD Cross! Entry: {price:.2f}")
                print(f"   ➡ Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f}")
                print(f"   ➡ Position Size: {pos_size} units")
                print(f"   ➡ Risk Amount: ${risk_amount:.2f}, Risk per unit: ${risk_per_unit:.2f}")
                self.buy(size=pos_size, sl=stop_loss, tp=take_profit)
        
        # Short Entry: MACD crosses below Signal
        elif (macd_prev >= signal_prev and 
              macd_current < signal_current and 
              not self.position):
            
            # Set stop loss and take profit
            stop_loss = price + atr
            take_profit = price - (1.5 * atr)  # 1:1.5 risk/reward
            
            # Calculate position size
            risk_per_unit = stop_loss - price
            pos_size = int(risk_amount / risk_per_unit) if risk_per_unit > 0 else 0
            
            if pos_size > 0 and take_profit < price < stop_loss:
                print(f"🌙🚀 [SHORT ENTRY] Solana Dev spotted a Bearish MACD Cross! Entry: {price:.2f}")
                print(f"   ➡ Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f}")
                print(f"   ➡ Position Size: {pos_size} units")
                print(f"   ➡ Risk Amount: ${risk_amount:.2f}, Risk per unit: ${risk_per_unit:.2f}")
                self.sell(size=pos_size, sl=stop_loss, tp=take_profit)

if __name__ == "__main__":
    # Load and prepare data
    df = load_and_clean_data()
    
    # Run backtest
    bt = Backtest(df, MACDCrossover, cash=100000, commission=.002)
    stats = bt.run()
    
    # Print and save results
    print("\n✨ Backtest Results:")
    print(f"Return: {stats['Return [%]']:.2f}%")
    print(f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
    print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate: {stats['Win Rate [%]']:.2f}%")
    
    # Save stats
    stats_file = os.path.join(STATS_DIR, f"MACDCrossover_stats_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt")
    print(f"\n📊 Stats saved to: {stats_file}")
    with open(stats_file, 'w') as f:
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")
    
    # Plot and save chart
    chart_file = os.path.join(CHARTS_DIR, f"MACDCrossover_chart_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.html")
    bt.plot(filename=chart_file, open_browser=False)
    print(f"📈 Chart saved to: {chart_file}") 