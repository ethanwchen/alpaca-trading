import socket
import json
from collections import deque
import numpy as np
import time

class TradingClient:
    def __init__(self, market_host="127.0.0.1", market_port=9995, trading_host="127.0.0.1", trading_port=9999):
        self.market_host = market_host
        self.market_port = market_port
        self.trading_host = trading_host
        self.trading_port = trading_port
        self.price_history = {}
        self.last_trade_price = {}
        self.last_trade_time = {}

    def connect_to_market(self):
        """Connects to port 9995 to receive market data."""
        try:
            self.market_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.market_socket.connect((self.market_host, self.market_port))
            print(f"Connected to market data at {self.market_host}:{self.market_port}")
        except Exception as e:
            print(f"Failed to connect to market data: {e}")
            return False
        return True

    def connect_to_trading(self):
        """Connects to port 9999 to send trade orders."""
        try:
            self.trading_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.trading_socket.connect((self.trading_host, self.trading_port))
            print(f"Connected to trading system at {self.trading_host}:{self.trading_port}")
        except Exception as e:
            print(f"Failed to connect to trading system: {e}")
            return False
        return True

    def receive_market_data(self):
        """Receives and processes market data from port 9995."""
        try:
            while True:
                data = self.market_socket.recv(4096).decode("utf-8")
                if not data:
                    print("Market server disconnected.")
                    break

                order = json.loads(data.strip())
                self.process_market_data(order)

        except Exception as e:
            print(f"Error receiving market data: {e}")
        finally:
            self.market_socket.close()

    def process_market_data(self, order):
        """Processes the incoming order and updates historical data."""
        symbol = order["Symbol"]
        price = float(order["Price"])
        exchange = order["Exchange"]

        # Store price history for moving averages
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=10)  # Track last 10 prices
        self.price_history[symbol].append(price)

        trade = self.mean_reversion_trade(symbol, price, exchange)
        if trade:
            self.send_trade_order(trade)

    def calculate_atr(self, prices):
        """Calculates ATR using NumPy."""
        if len(prices) < 2:
            return 1
        return np.mean(np.abs(np.diff(prices)))

    def mean_reversion_trade(self, symbol, price, exchange):
        if symbol not in self.price_history or len(self.price_history[symbol]) < 5:
            return None  # Not enough data to make a decision

        prices = np.array(self.price_history[symbol])
        avg_price = np.mean(prices)
        std_dev = np.std(prices)

        lower_band = avg_price - (2 * std_dev)
        upper_band = avg_price + (2 * std_dev)

        base_trade_size = 2000
        atr = self.calculate_atr(prices)
        trade_size = int(base_trade_size * (10 / max(atr, 1)))

        if symbol not in self.last_trade_price:
            self.last_trade_price[symbol] = price # Initialize with first price

        if symbol in self.last_trade_price and self.last_trade_price[symbol] is not None and abs(
                price - self.last_trade_price[symbol]) < 0.5:
            return None

        if price < lower_band:
            print(f"BUY {symbol} at {price} (Lower Band: {lower_band:.4f})")
            self.last_trade_price[symbol] = price
            self.last_trade_time[symbol] = time.time()
            return {"Symbol": symbol, "Exchange": exchange, "Quantity": trade_size, "Side": "B",
                    "Price": round(price, 4)}

        elif price > upper_band:
            print(f"SELL {symbol} at {price} (Upper Band: {upper_band:.4f})")
            self.last_trade_price[symbol] = price
            self.last_trade_time[symbol] = time.time()
            return {"Symbol": symbol, "Exchange": exchange, "Quantity": trade_size, "Side": "S",
                    "Price": round(price, 4)}
        return None

    def send_trade_order(self, order):
        """Sends a trade order to port 9999."""
        try:
            message = json.dumps(order)
            self.trading_socket.sendall(message.encode("utf-8"))
            print(f"Sent trade order: {message}")

            response = self.trading_socket.recv(1024).decode("utf-8")
            print(f"Trade Execution Response: {response}")

        except Exception as e:
            print(f"Failed to send trade order: {e}")

    def start(self):
        """Starts the trading bot."""
        if not self.connect_to_market():
            return
        if not self.connect_to_trading():
            return
        self.receive_market_data()

if __name__ == "__main__":
    client = TradingClient()
    client.start()
