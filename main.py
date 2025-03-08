# main.py

import socket
import json
import threading
import time

from order_book import OrderBook
from liquidity_model import get_liquidity_signal
from news_sentiment_model import FinBertSentimentModel
from mean_reversion_model import MeanReversionModel
from decision_maker import decision_maker
from tcp_client import send_order

# Global model instances
order_book = OrderBook()
finbert_model = FinBertSentimentModel()
mean_rev_model = MeanReversionModel(window=10)

# Lock to ensure only one order is placed at a time
order_placement_lock = threading.Lock()

def process_market_data(data):
    """
    Process incoming market data by:
      1. Parsing the JSON message.
      2. Normalizing keys (ensuring "Price", "Symbol", etc. are present).
      3. Making a defensive copy of the order so that later mutations (in the order book)
         do not affect our processing.
      4. Updating the order book.
      5. Updating the mean reversion model.
      6. Generating a FinBERT-based sentiment signal.
      7. Calculating a liquidity signal.
      8. Combining these signals via the decision maker (which selects the best exchange, price, and quantity for profit maximization).
      9. If a decision is reached and no order is in progress, sending the order.
    """
    try:
        order = json.loads(data.strip())
    except json.JSONDecodeError as e:
        print("JSON parse error:", e)
        return

    # Make a defensive copy so that mutations in the order book do not affect our local copy.
    local_order = order.copy()

    # Normalize key names in case some orders use lowercase keys
    if "Price" not in local_order and "price" in local_order:
        local_order["Price"] = local_order["price"]
    if "Symbol" not in local_order and "symbol" in local_order:
        local_order["Symbol"] = local_order["symbol"]
    if "Description" not in local_order and "description" in local_order:
        local_order["Description"] = local_order["description"]
    if "News" not in local_order and "news" in local_order:
        local_order["News"] = local_order["news"]

    # Check if "Price" is present; if not, skip this order.
    if "Price" not in local_order:
        print(f"Skipping order for {local_order.get('Symbol', 'UNKNOWN')} because 'Price' is missing.")
        return

    symbol = local_order.get("Symbol", "UNKNOWN")
    description = local_order.get("Description", "")
    news_code = local_order.get("News", "0")
    
    try:
        # Try to extract the price; if missing or invalid, skip this order.
        current_price = float(local_order["Price"])
    except (KeyError, ValueError) as e:
        print(f"Skipping order for {symbol} due to missing or invalid 'Price': {e}")
        return

    # 1) Update the order book with this market update (use our defensive copy)
    order_book.update_order(local_order)

    # 2) Update the mean reversion model with the current price
    mean_rev_model.update(symbol, current_price)
    mean_signal = mean_rev_model.get_signal(symbol, current_price)

    # 3) Use FinBERT to derive a sentiment signal based on the description and news code
    news_signal = finbert_model.get_sentiment_signal(description, news_code)

    # 4) Compute a liquidity signal from the order book
    liquidity_signal = get_liquidity_signal(order_book, symbol)

    print(f"Signals for {symbol} => News: {news_signal}, Liquidity: {liquidity_signal}, MeanRev: {mean_signal}")

    # 5) Make a trading decision using the combined signals and profit-maximizing logic.
    decision = decision_maker(news_signal, liquidity_signal, mean_signal, order_book, symbol, current_price)
    if decision:
        # Only send one order at a time
        if order_placement_lock.acquire(blocking=False):
            try:
                print("Final decision:", decision)
                send_order(decision)
            finally:
                order_placement_lock.release()
        else:
            print("Order already in progress. Skipping.")
    else:
        print(f"No consensus for {symbol}")

def listen_to_market_feed():
    """
    Connects to the market data feed on port 9995 and processes each newline-delimited JSON message.
    """
    HOST = "127.0.0.1"
    PORT = 9995
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((HOST, PORT))
        print(f"Connected to market data feed at {HOST}:{PORT}")
    except Exception as e:
        print("Could not connect to market data feed:", e)
        return

    while True:
        try:
            data = client.recv(4096).decode()
            if not data:
                break
            # Assume each message is newline-separated
            for message in data.strip().split("\n"):
                try:
                    process_market_data(message)
                except Exception as me:
                    print("Error processing message, skipping:", me)
                    continue
        except Exception as e:
            print("Error receiving data:", e)
            continue

    client.close()

if __name__ == "__main__":
    # Start listening to market data in a background thread
    threading.Thread(target=listen_to_market_feed, daemon=True).start()

    # Keep main thread alive so the background thread continues running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down.")
