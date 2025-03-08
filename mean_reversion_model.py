from collections import deque
import numpy as np

class MeanReversionModel:
    def __init__(self, window=10):
        self.window = window
        # Maintain a deque for each symbol (maxlen equals the window size).
        self.price_history = {}

    def update(self, symbol, price):
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.window)
        self.price_history[symbol].append(price)

    def get_signal(self, symbol, price):
        """
        Generates a mean reversion signal:
          +1 -> Price is below the lower band (buy signal)
          -1 -> Price is above the upper band (sell signal)
           0 -> Price is within the bands (no signal)
        """
        if symbol not in self.price_history or len(self.price_history[symbol]) < 5:
            return 0  # Not enough data
        prices = np.array(self.price_history[symbol])
        avg_price = np.mean(prices)
        std_dev = np.std(prices)
        lower_band = avg_price - (2 * std_dev)
        upper_band = avg_price + (2 * std_dev)

        if price < lower_band:
            return 1
        elif price > upper_band:
            return -1
        else:
            return 0
        
import alpaca_trade_api as tradeapi
import os
from dotenv import load_dotenv

# load API credentials
load_dotenv()
api_key = os.getenv("alpaca_api_key")
api_secret = os.getenv("alpaca_api_secret")
base_url = os.getenv("alpaca_base_url")

# initialize Alpaca API
api = tradeapi.REST(api_key, api_secret, base_url, api_version="v2")

def get_latest_price(symbol):
    """Fetch the latest market price from Alpaca."""
    bar = api.get_latest_bar(symbol)  # Get latest price
    return bar.c  # Return closing price
