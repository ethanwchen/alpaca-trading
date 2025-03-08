import alpaca_trade_api as tradeapi
import pandas as pd
import pickle
import os

# Set API credentials
API_KEY = "PKPG3N3MF2AKUFGWDKFG"
API_SECRET = "xhVMbvi3DJkoCWWeXNoYqC0FTWb9o7iST9ASzix8"
BASE_URL = "https://paper-api.alpaca.markets/"  # Paper trading URL

# Initialize Alpaca API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL)

# Create a folder for data storage
DATA_DIR = "market_data"
os.makedirs(DATA_DIR, exist_ok=True)

# Fetch active tradable assets
symbols = [asset.symbol for asset in api.list_assets(status="active") if asset.tradable]
print(f"Successfully fetched {len(symbols)} tradable assets.")

# Fetch & Store Market Data
for stock in symbols[:100]:  # Limit to 100 stocks for efficiency
    try:
        bars = api.get_bars(stock, "1D").df.reset_index()
        if not bars.empty:
            file_path_csv = os.path.join(DATA_DIR, f"{stock}.csv")
            file_path_pkl = os.path.join(DATA_DIR, f"{stock}.pkl")

            bars.to_csv(file_path_csv, index=False)
            with open(file_path_pkl, "wb") as f:
                pickle.dump(bars, f)
        else:
            print(f"No data for {stock}. Skipping.")
    except Exception as e:
        print(f"Error fetching {stock}: {e}")