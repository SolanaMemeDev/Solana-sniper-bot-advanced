#!/usr/bin/env python3
"""
Solana Dev's ATR MeanReversion Strategy Backtest 🌙✨
This strategy uses Keltner Channels (20-period SMA ± multiplier*STDDEV) and ATR for risk management.
It looks for when price pokes outside a Keltner Channel, then checks for a reversal candlestick pattern.
"""

import os
import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np
from backtesting.lib import crossover
import datetime

# Define directory paths
BASE_DIR = os.path.join("src", "data", "rbi")
DATA_PATH = os.path.join(BASE_DIR, "BTC-USD-15m.csv")
STATS_DIR = os.path.join(BASE_DIR, "backtests", "stats")
CHARTS_DIR = os.path.join(BASE_DIR, "backtests", "charts")

# Create directories if they don't exist
os.makedirs(STATS_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)

def load_and_clean_data(file_path):
    """Load and clean the data from CSV"""
    print(f"🌙 Loading data from {file_path}")
    df = pd.read_csv(file_path)
    
    # Clean column names - remove spaces and convert to lowercase
    df.columns = df.columns.str.strip().str.lower()
    
    # Rename columns to match Backtesting requirements
    df = df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    
    # Drop any unnamed columns
    df = df.drop(columns=[col for col in df.columns if 'Unnamed' in col])
    
    # Ensure we have all required columns
    required_columns = ['Open', 'High', 'Low', 'Close']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"Missing required columns. Data must have columns: {required_columns}")
        
    # Convert datetime to index
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    
    return df[required_columns + (['Volume'] if 'Volume' in df.columns else [])]

class ATRMeanReversion(Strategy):
    """ATR Mean Reversion Strategy by Solana Dev 🌙"""
    
    kelter_period = 20
    kelter_multiplier = 1.5
    atr_period = 14
    risk_per_trade = 0.02  # 2% risk per trade
    min_position_size = 1.0
    
    def init(self):
        """Initialize the strategy with indicators"""
        print("🌙✨ Initializing Solana Dev's ATR Mean Reversion Strategy")
        
        # Calculate Keltner Channels
        self.kc_middle = self.I(lambda: pd.Series(self.data.Close).rolling(self.kelter_period).mean())
        atr = self.I(lambda: pd.Series(self.data.Close).rolling(self.atr_period).std())
        self.kc_upper = self.I(lambda: self.kc_middle + (atr * self.kelter_multiplier))
        self.kc_lower = self.I(lambda: self.kc_middle - (atr * self.kelter_multiplier))
        
        # Track our position state
        self.entry_price = 0
        self.stop_loss = 0
        self.take_profit = 0
        self.position_size = 0
        
    def next(self):
        """Define the trading logic for each candle"""
        curr_close = self.data.Close[-1]
        curr_open = self.data.Open[-1]
        
        # Print current candle info
        print(f"🌙✨ [BAR] Current Candle >> Open: {curr_open:.2f}, High: {self.data.High[-1]:.2f}, "
              f"Low: {self.data.Low[-1]:.2f}, Close: {curr_close:.2f}")
        
        # Print Keltner Channel levels
        print(f"🌙✨ [LEVELS] Upper: {self.kc_upper[-1]:.2f}, Lower: {self.kc_lower[-1]:.2f}, "
              f"ATR: {(self.kc_upper[-1] - self.kc_lower[-1])/3:.2f}")
        
        try:
            # Calculate position size and risk
            atr = self.kc_upper[-1] - self.kc_lower[-1]
            equity = self.equity
            risk_amount = equity * self.risk_per_trade
            
            # Long Entry Conditions
            if not self.position and curr_close > curr_open and curr_close < self.kc_lower[-1]:
                # Calculate entry parameters
                entry_price = curr_close
                stop_loss = entry_price - atr
                take_profit = entry_price + (atr * 1.5)
                
                # Calculate position size
                risk_per_unit = abs(entry_price - stop_loss)
                position_size = max(int(risk_amount / risk_per_unit), self.min_position_size)
                
                print(f"🌙🚀 [LONG ENTRY] Solana Dev spotted a Bullish Signal! Entry: {entry_price:.2f}")
                print(f"   ➡ Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f}")
                print(f"   ➡ Position Size: {position_size} units")
                print(f"   ➡ Risk Amount: ${risk_amount:.2f}, Risk per unit: ${risk_per_unit:.2f}")
                
                self.buy(size=position_size, sl=stop_loss, tp=take_profit)
                self.entry_price = entry_price
                self.position_size = position_size
            
            # Short Entry Conditions
            elif not self.position and curr_close < curr_open and curr_close > self.kc_upper[-1]:
                # Calculate entry parameters
                entry_price = curr_close
                stop_loss = entry_price + atr
                take_profit = entry_price - (atr * 1.5)
                
                # Calculate position size
                risk_per_unit = abs(stop_loss - entry_price)
                position_size = max(int(risk_amount / risk_per_unit), self.min_position_size)
                
                print(f"🌙🚀 [SHORT ENTRY] Solana Dev spotted a Bearish Signal! Entry: {entry_price:.2f}")
                print(f"   ➡ Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f}")
                print(f"   ➡ Position Size: {position_size} units")
                print(f"   ➡ Risk Amount: ${risk_amount:.2f}, Risk per unit: ${risk_per_unit:.2f}")
                
                self.sell(size=position_size, sl=stop_loss, tp=take_profit)
                self.entry_price = entry_price
                self.position_size = position_size
                
        except Exception as e:
            print(f"⚠️ Error in strategy execution: {str(e)}")

if __name__ == "__main__":
    # Set up paths
    data_path = "src/data/rbi/BTC-USD-15m.csv"
    stats_dir = "src/data/rbi/backtests/stats"
    charts_dir = "src/data/rbi/backtests/charts"
    
    # Create directories if they don't exist
    os.makedirs(stats_dir, exist_ok=True)
    os.makedirs(charts_dir, exist_ok=True)
    
    # Load data and run backtest
    data = load_and_clean_data(data_path)
    bt = Backtest(data, ATRMeanReversion, cash=1_000_000, commission=.002)
    
    try:
        stats = bt.run()
        print("\n🌙✨ Backtest Results:")
        print(f"Return: {stats['Return [%]']:.2f}%")
        print(f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
        print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
        print(f"Win Rate: {stats['Win Rate [%]']:.2f}%")
        
        # Save stats
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        stats_file = os.path.join(stats_dir, f"ATRMeanReversion_stats_{timestamp}.txt")
        with open(stats_file, "w") as f:
            f.write(str(stats))
        print(f"\n📊 Stats saved to: {stats_file}")
        
        # Plot and save chart
        chart_file = os.path.join(charts_dir, f"ATRMeanReversion_chart_{timestamp}.html")
        bt.plot(filename=chart_file, open_browser=False)
        print(f"📈 Chart saved to: {chart_file}")
        
    except Exception as e:
        print(f"⚠️ Error running backtest: {str(e)}")
