#!/usr/bin/env python
"""
Bollinger Bands Strategy 🎯
A mean reversion strategy that uses Bollinger Bands to identify overbought and oversold conditions.
When price touches the lower band and shows reversal, we go long.
When price touches the upper band and shows reversal, we go short.
Created by Solana Dev with 🌙✨
"""

import os
import pandas as pd
import numpy as np
import talib
from backtesting import Strategy, Backtest

# Directory setup
BASE_DIR = "src/data/rbi"
DATA_PATH = os.path.join(BASE_DIR, "BTC-USD-15m.csv")
STATS_DIR = os.path.join(BASE_DIR, "backtests/stats")
CHARTS_DIR = os.path.join(BASE_DIR, "backtests/charts")

def load_and_clean_data():
    """Load and clean the OHLCV data"""
    print("🌙 Solana Dev is loading the data...")
    df = pd.read_csv(DATA_PATH)
    
    # Drop unnamed columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Clean column names - strip spaces and convert to lowercase
    df.columns = df.columns.str.strip().str.lower()
    
    # Check required columns
    required_cols = ['open', 'high', 'low', 'close']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Data must contain columns: {required_cols}")
    
    # Convert datetime and set as index
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    
    # Rename columns with proper capitalization for Backtesting library
    column_map = {
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }
    df = df.rename(columns=column_map)
    
    print("✨ Data loaded successfully!")
    print(f"🔍 Columns: {df.columns.tolist()}")
    return df

class BollingerBandsStrategy(Strategy):
    """
    Bollinger Bands Strategy Implementation
    - Uses 20-period SMA with 2 standard deviations for the bands
    - RSI for confirmation of reversal
    - ATR for position sizing
    """
    
    n_sma = 14  # Shorter period for faster signals
    n_std = 2.5  # Wider bands for stronger signals
    n_atr = 14  # Period for ATR
    n_rsi = 14  # Period for RSI
    
    risk_per_trade = 0.01  # Reduced risk to 1% per trade for more conservative approach
    
    def init(self):
        """Initialize indicators"""
        print("🌙 Solana Dev is calculating indicators...")
        
        # Calculate Bollinger Bands
        self.sma = self.I(talib.SMA, self.data.Close, timeperiod=self.n_sma)
        self.std = self.I(talib.STDDEV, self.data.Close, timeperiod=self.n_sma)
        self.upper = self.I(lambda: self.sma + self.n_std * self.std)
        self.lower = self.I(lambda: self.sma - self.n_std * self.std)
        
        # Calculate RSI for confirmation
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.n_rsi)
        
        # Calculate ATR for position sizing
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.n_atr)
        
        print("✨ Indicators calculated successfully!")
    
    def next(self):
        """Define trading logic for each candle"""
        
        # Skip if not enough data for all our calculations
        required_bars = max(self.n_sma, self.n_rsi, self.n_atr, 3)  # Need at least 3 bars for momentum
        if len(self.data) < required_bars:
            return
        
        # Skip if any indicator is NaN
        if (np.isnan(self.upper[-1]) or np.isnan(self.lower[-1]) or 
            np.isnan(self.rsi[-1]) or np.isnan(self.atr[-1])):
            return
            
        # Current price and indicators
        price = self.data.Close[-1]
        prev_price = self.data.Close[-2]
        prev_price2 = self.data.Close[-3]
        upper = self.upper[-1]
        lower = self.lower[-1]
        rsi = self.rsi[-1]
        sma = self.sma[-1]
        
        # Calculate position size based on ATR
        atr = self.atr[-1]
        account_value = self.equity
        risk_amount = account_value * self.risk_per_trade
        
        # For long positions - price below lower band + RSI oversold + momentum confirmation
        if (price < lower and rsi < 40 and 
            price > prev_price and prev_price > prev_price2):  # Confirmed upward momentum
            
            entry = price
            stop_loss = entry - (1.5 * atr)  # Wider stop loss
            take_profit = entry + (3 * atr)  # 1:2 risk-reward
            
            risk_per_unit = entry - stop_loss
            pos_size = int(risk_amount / risk_per_unit) if risk_per_unit > 0 else 0
            
            if pos_size > 0 and not self.position:  # Check we're not already in a position
                print(f"🌙🚀 [LONG ENTRY] Solana Dev spotted a Bullish BB Signal! Entry: {entry:.2f}")
                print(f"   ➡ Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f}")
                print(f"   ➡ Position Size: {pos_size} units")
                print(f"   ➡ Risk Amount: ${risk_amount:.2f}, Risk per unit: ${risk_per_unit:.2f}")
                self.buy(size=pos_size, sl=stop_loss, tp=take_profit)
        
        # For short positions - price above upper band + RSI overbought + momentum confirmation
        elif (price > upper and rsi > 60 and 
              price < prev_price and prev_price < prev_price2):  # Confirmed downward momentum
            
            entry = price
            stop_loss = entry + (1.5 * atr)  # Wider stop loss
            take_profit = entry - (3 * atr)  # 1:2 risk-reward
            
            risk_per_unit = stop_loss - entry
            pos_size = int(risk_amount / risk_per_unit) if risk_per_unit > 0 else 0
            
            if pos_size > 0 and not self.position:  # Check we're not already in a position
                print(f"🌙🚀 [SHORT ENTRY] Solana Dev spotted a Bearish BB Signal! Entry: {entry:.2f}")
                print(f"   ➡ Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f}")
                print(f"   ➡ Position Size: {pos_size} units")
                print(f"   ➡ Risk Amount: ${risk_amount:.2f}, Risk per unit: ${risk_per_unit:.2f}")
                self.sell(size=pos_size, sl=stop_loss, tp=take_profit)

if __name__ == "__main__":
    # Create directories if they don't exist
    os.makedirs(STATS_DIR, exist_ok=True)
    os.makedirs(CHARTS_DIR, exist_ok=True)
    
    # Load data
    data = load_and_clean_data()
    
    # Run backtest
    bt = Backtest(data, BollingerBandsStrategy, cash=1_000_000, commission=.002)
    stats = bt.run()
    
    # Print and save results
    print("\n✨ Backtest Results:")
    print(f"Return: {stats['Return [%]']:.2f}%")
    print(f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
    print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate: {stats['Win Rate [%]']:.2f}%")
    
    # Save stats
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    stats_file = os.path.join(STATS_DIR, f"BollingerBands_stats_{timestamp}.txt")
    with open(stats_file, 'w') as f:
        for k, v in stats.items():
            f.write(f"{k}: {v}\n")
    print(f"\n📊 Stats saved to: {stats_file}")
    
    # Save chart
    chart_file = os.path.join(CHARTS_DIR, f"BollingerBands_chart_{timestamp}.html")
    bt.plot(filename=chart_file, open_browser=False)
    print(f"📈 Chart saved to: {chart_file}") 