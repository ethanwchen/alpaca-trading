import os
import alpaca_trade_api as tradeapi
import time
import logging
import threading
from dotenv import load_dotenv
from mean_reversion_model import MeanReversionModel, get_latest_price
from news_sentiment_model import FinBertSentimentModel
from order_book import OrderBook

# setup logging
log_file = "trading_log.txt"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# load api credentials
load_dotenv()
api_key = os.getenv("alpaca_api_key")
api_secret = os.getenv("alpaca_api_secret")
base_url = os.getenv("alpaca_base_url")

# initialize api
api = tradeapi.REST(api_key, api_secret, base_url, api_version="v2")

# List of symbols to trade
symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]
mean_rev_model = MeanReversionModel()
sentiment_model = FinBertSentimentModel()
order_book = OrderBook()

# Initialize order book with sample orders for each symbol
for symbol in symbols:
    test_bid = {
        "OrderID": f"bid001_{symbol}",
        "Symbol": symbol,
        "Side": "B",
        "Quantity": "100",
        "Price": "180.50"
    }
    test_ask = {
        "OrderID": f"ask001_{symbol}",
        "Symbol": symbol,
        "Side": "S",
        "Quantity": "50",
        "Price": "181.00"
    }
    order_book.add_order(test_bid)
    order_book.add_order(test_ask)

def decision_maker(symbol):
    """fetch market data, generate signals, and execute trades."""
    
    try:
        # step 1: get real-time stock price
        latest_price = get_latest_price(symbol)
        mean_rev_model.update(symbol, latest_price)

        # step 2: generate model signals
        mean_rev_signal = mean_rev_model.get_signal(symbol, latest_price)
        
        # Get news sentiment with symbol name
        news_signal = sentiment_model.get_sentiment_signal(
            description=f"{symbol} stock performance update", 
            news_value="50"
        )
        
        # Log detailed model signals for debugging
        logging.info(f"Model signals for {symbol}: Mean Reversion = {mean_rev_signal}, " +
                    f"News Sentiment = {news_signal}, Liquidity = {order_book.get_liquidity_signal(symbol)}")
        
        liquidity_signal = order_book.get_liquidity_signal(symbol)  # fetch liquidity signal

        # step 3: decide trade action
        signals = [news_signal, liquidity_signal, mean_rev_signal]
        buy_votes = signals.count(1)
        sell_votes = signals.count(-1)
        
        if buy_votes >= 2:
            api.submit_order(
                symbol=symbol,
                qty=1,
                side="buy",
                type="market",
                time_in_force="gtc"
            )
            logging.info(f"buy order placed for {symbol} at {latest_price}")

        elif sell_votes >= 2:
            api.submit_order(
                symbol=symbol,
                qty=1,
                side="sell",
                type="market",
                time_in_force="gtc"
            )
            logging.info(f"sell order placed for {symbol} at {latest_price}")

        else:
            logging.info(f"no trade executed for {symbol} - signals not aligned.")
    
    except Exception as e:
        logging.error(f"error occurred for {symbol}: {str(e)}")

def run_trading_cycle():
    """Run the decision maker for all symbols."""
    for symbol in symbols:
        decision_maker(symbol)

# run trading cycle every minute
while True:
    try:
        run_trading_cycle()
    except Exception as e:
        logging.error(f"error in trading cycle: {str(e)}")
    time.sleep(60)  # wait for 1 minute before running again