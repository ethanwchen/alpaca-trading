import pandas as pd
import glob
import os

# Define directory for market data
DATA_DIR = "market_data"
csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))

# Load market data
stock_data = {os.path.splitext(os.path.basename(f))[0]: pd.read_csv(f) for f in csv_files}

# Compute Indicators
trade_signals = {}
for stock, df in stock_data.items():
    if df.empty:
        print(f"Skipping {stock}: No data available.")
        continue

    df["SMA_50"] = df["close"].rolling(50).mean()
    df["SMA_200"] = df["close"].rolling(200).mean()
    price_diff = df["close"].diff().rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + price_diff / abs(price_diff)))
    df["MACD"] = df["close"].ewm(span=12).mean() - df["close"].ewm(span=26).mean()

    df.dropna(inplace=True)
    if df.empty:
        print(f"Skipping {stock}: No data after dropping NaN.")
        continue

    latest = df.iloc[-1]
    print(f"\n{stock} Indicators:")
    print(f"SMA_50: {latest['SMA_50']:.2f}, SMA_200: {latest['SMA_200']:.2f}, RSI: {latest['RSI']:.2f}, MACD: {latest['MACD']:.2f}")

    trade_signals[stock] = "buy" if latest["SMA_50"] > latest["SMA_200"] and latest["RSI"] < 40 else \
                           "sell" if latest["SMA_50"] < latest["SMA_200"] or latest["RSI"] > 60 else "hold"
