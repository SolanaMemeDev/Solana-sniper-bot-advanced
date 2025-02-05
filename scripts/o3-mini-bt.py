"""
Trading Bot Using VWAP Strategy with Backtesting.py

This script:
    1. Downloads historical data from Yahoo Finance (for example, AAPL from 2020 to 2024).
    2. Defines a trading strategy based on the VWAP indicator.
    3. Backtests the strategy using backtesting.py.
    4. Prints out the performance statistics and plots the results.

Note:
    Since true intraday VWAP isn’t available with daily data, we use a rolling VWAP 
    (computed over the last 14 days by default) as a proxy.


This was my first O3 Mini test here and it only took me two different tries in order to get this back to us to work. So O3 Mini is far. 
"""

import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy
import matplotlib.pyplot as plt

def vwap_indicator(high, low, close, volume, window=14):
    """
    Compute the Volume Weighted Average Price (VWAP) as a rolling indicator.
    
    Because backtesting.py passes NumPy arrays to indicators, we first convert the inputs
    to pandas Series so we can use the rolling window functionality.
    
    For each rolling window of the specified period, VWAP is computed as:
        VWAP = (sum(typical_price * volume) over window) / (sum(volume) over window)
    where the typical_price is defined as (high + low + close) / 3.
    
    :param high: NumPy array of high prices.
    :param low: NumPy array of low prices.
    :param close: NumPy array of close prices.
    :param volume: NumPy array of volume.
    :param window: integer, the size of the rolling window.
    :return: NumPy array of VWAP values.
    """
    # Compute the typical price
    typical_price = (high + low + close) / 3.0

    # Convert inputs to pandas Series to use rolling window calculations
    tp_series = pd.Series(typical_price)
    volume_series = pd.Series(volume)

    # Compute the rolling sums with a minimum period of 1 to avoid NaN at the beginning
    rolling_vp = (tp_series * volume_series).rolling(window=window, min_periods=1).sum()
    rolling_volume = volume_series.rolling(window=window, min_periods=1).sum()
    
    # Compute VWAP and return it as a NumPy array
    vwap = rolling_vp / rolling_volume
    return vwap.values

class VWAPStrategy(Strategy):
    """
    A simple strategy that uses a rolling VWAP indicator:
      - Buy when the closing price crosses above the VWAP.
      - Sell (or exit) when the closing price crosses below the VWAP.
    """
    # Define the rolling window period for the VWAP calculation.
    vwap_window = 14

    def init(self):
        """
        Initialization of the strategy.
        The indicator is registered with self.I(), which makes it available as self.vwap.
        """
        self.vwap = self.I(vwap_indicator,
                           self.data.High,
                           self.data.Low,
                           self.data.Close,
                           self.data.Volume,
                           self.vwap_window)

    def next(self):
        """
        Called on every new bar. Implements the trading logic:
          - If the close is above VWAP and no open position exists, then buy.
          - If the close is below VWAP and there is an open position, then close the position.
        """
        # If the current closing price is above the VWAP and we have no open position, then buy.
        if self.data.Close[-1] > self.vwap[-1] and not self.position:
            self.buy()
        # If the current closing price is below the VWAP and we are in a position, then exit.
        elif self.data.Close[-1] < self.vwap[-1] and self.position:
            self.position.close()

if __name__ == '__main__':
    # -------------------------------
    # Step 1: Download Historical Data
    # -------------------------------
    ticker = 'AAPL'
    start_date = '2020-01-01'
    end_date = '2024-01-01'
    print(f"Downloading data for {ticker} from {start_date} to {end_date}...")
    
    # Download data from Yahoo Finance
    data = yf.download(ticker, start=start_date, end=end_date)
    
    # Check if data was downloaded successfully
    if data.empty:
        print("No data downloaded. Please check the ticker symbol and date range.")
        exit()
    else:
        data.dropna(inplace=True)
        print("Data download complete. Here is a sample:")
        print(data.head())
    
    # -------------------------------
    # Step 2: Set Up and Run the Backtest
    # -------------------------------
    print("\nStarting backtest using the VWAP strategy...")
    bt = Backtest(data, 
                  VWAPStrategy, 
                  cash=10000,          # Starting capital
                  commission=0.002,    # Commission per trade (0.2%)
                  trade_on_close=True) # Execute trades at the close of the bar
    
    # Run the backtest; bt.run() returns a statistics report
    stats = bt.run()
    
    # -------------------------------
    # Step 3: Output Backtest Results
    # -------------------------------
    print("\nBacktest Results:")
    print(stats)
    
    # -------------------------------
    # Step 4: Plot the Backtest
    # -------------------------------
    bt.plot()
