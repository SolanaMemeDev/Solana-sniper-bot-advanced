#!/usr/bin/env python3
"""
Solana Dev's RSI Divergence Strategy Backtest 🌙✨
This strategy looks for divergences between price action and RSI indicator.
Bullish divergence: Lower lows in price but higher lows in RSI
Bearish divergence: Higher highs in price but lower highs in RSI
"""

import os
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
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
    
    # Convert datetime to index
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    
    return df

def find_divergences(price_data, rsi_data, window=5):
    """Find bullish and bearish divergences"""
    bullish_div = []
    bearish_div = []
    
    # Convert to numpy arrays for faster processing
    price_arr = np.array(price_data)
    rsi_arr = np.array(rsi_data)
    
    for i in range(window, len(price_arr)):
        # Get price and RSI windows
        price_window = price_arr[i-window:i+1]
        rsi_window = rsi_arr[i-window:i+1]
        
        # Skip if we have any NaN values
        if np.isnan(price_window).any() or np.isnan(rsi_window).any():
            bullish_div.append(0)
            bearish_div.append(0)
            continue
        
        # Check for bullish divergence (price lower lows, RSI higher lows)
        if price_window[-1] <= price_window.min() and rsi_window[-1] > rsi_window.min():
            bullish_div.append(1)
        else:
            bullish_div.append(0)
            
        # Check for bearish divergence (price higher highs, RSI lower highs)
        if price_window[-1] >= price_window.max() and rsi_window[-1] < rsi_window.max():
            bearish_div.append(1)
        else:
            bearish_div.append(0)
            
    # Pad the beginning with zeros
    bullish_div = [0] * window + bullish_div
    bearish_div = [0] * window + bearish_div
    
    return np.array(bullish_div), np.array(bearish_div)

class RSIDivergence(Strategy):
    """RSI Divergence Strategy by Solana Dev 🌙"""
    
    # Strategy parameters
    rsi_period = 14
    rsi_overbought = 70
    rsi_oversold = 30
    divergence_window = 5
    risk_per_trade = 0.02  # 2% risk per trade
    atr_period = 14
    atr_multiplier = 2.0
    
    def init(self):
        """Initialize strategy indicators"""
        print("🌙✨ Initializing Solana Dev's RSI Divergence Strategy")
        
        # Calculate RSI
        close_values = np.array(self.data.Close)
        self.rsi = self.I(lambda: talib.RSI(close_values, timeperiod=self.rsi_period))
        
        # Calculate ATR for position sizing
        high_values = np.array(self.data.High)
        low_values = np.array(self.data.Low)
        self.atr = self.I(lambda: talib.ATR(high_values, low_values, 
                                           close_values, timeperiod=self.atr_period))
        
        # Find divergences
        self.bullish_div, self.bearish_div = self.I(lambda: find_divergences(
            close_values, self.rsi, self.divergence_window))
    
    def next(self):
        """Define trading logic for each candle"""
        
        # Print current candle info
        print(f"🌙✨ [BAR] Current Candle >> Open: {self.data.Open[-1]:.2f}, "
              f"High: {self.data.High[-1]:.2f}, Low: {self.data.Low[-1]:.2f}, "
              f"Close: {self.data.Close[-1]:.2f}")
        print(f"🌙✨ [RSI] Current: {self.rsi[-1]:.2f}")
        
        # Skip if not enough data
        if self.rsi[-1] == 0 or np.isnan(self.rsi[-1]):
            return
        
        try:
            # Calculate position size and risk
            atr = self.atr[-1]
            equity = self.equity
            risk_amount = equity * self.risk_per_trade
            
            # Long Entry on Bullish Divergence
            if not self.position and self.bullish_div[-1] and self.rsi[-1] < self.rsi_oversold:
                entry_price = self.data.Close[-1]
                stop_loss = entry_price - (atr * self.atr_multiplier)
                take_profit = entry_price + (atr * self.atr_multiplier * 1.5)
                
                # Calculate position size
                risk_per_unit = abs(entry_price - stop_loss)
                position_size = max(int(risk_amount / risk_per_unit), 1)
                
                print(f"🌙🚀 [LONG ENTRY] Solana Dev spotted a Bullish Divergence! Entry: {entry_price:.2f}")
                print(f"   ➡ Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f}")
                print(f"   ➡ Position Size: {position_size} units")
                print(f"   ➡ Risk Amount: ${risk_amount:.2f}, Risk per unit: ${risk_per_unit:.2f}")
                
                self.buy(size=position_size, sl=stop_loss, tp=take_profit)
            
            # Short Entry on Bearish Divergence
            elif not self.position and self.bearish_div[-1] and self.rsi[-1] > self.rsi_overbought:
                entry_price = self.data.Close[-1]
                stop_loss = entry_price + (atr * self.atr_multiplier)
                take_profit = entry_price - (atr * self.atr_multiplier * 1.5)
                
                # Calculate position size
                risk_per_unit = abs(stop_loss - entry_price)
                position_size = max(int(risk_amount / risk_per_unit), 1)
                
                print(f"🌙🚀 [SHORT ENTRY] Solana Dev spotted a Bearish Divergence! Entry: {entry_price:.2f}")
                print(f"   ➡ Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f}")
                print(f"   ➡ Position Size: {position_size} units")
                print(f"   ➡ Risk Amount: ${risk_amount:.2f}, Risk per unit: ${risk_per_unit:.2f}")
                
                self.sell(size=position_size, sl=stop_loss, tp=take_profit)
                
        except Exception as e:
            print(f"⚠️ Error in strategy execution: {str(e)}")

if __name__ == "__main__":
    # Load data and run backtest
    data = load_and_clean_data(DATA_PATH)
    bt = Backtest(data, RSIDivergence, cash=1_000_000, commission=.002)
    
    try:
        stats = bt.run()
        print("\n🌙✨ Backtest Results:")
        print(f"Return: {stats['Return [%]']:.2f}%")
        print(f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
        print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
        print(f"Win Rate: {stats['Win Rate [%]']:.2f}%")
        
        # Save stats
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        stats_file = os.path.join(STATS_DIR, f"RSIDivergence_stats_{timestamp}.txt")
        with open(stats_file, "w") as f:
            f.write(str(stats))
        print(f"\n📊 Stats saved to: {stats_file}")
        
        # Plot and save chart
        chart_file = os.path.join(CHARTS_DIR, f"RSIDivergence_chart_{timestamp}.html")
        bt.plot(filename=chart_file, open_browser=False)
        print(f"📈 Chart saved to: {chart_file}")
        
    except Exception as e:
        print(f"⚠️ Error running backtest: {str(e)}") 