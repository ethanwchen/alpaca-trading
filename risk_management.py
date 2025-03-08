import alpaca_trade_api as tradeapi
import pandas as pd
import glob
import os

# Set API credentials
API_KEY = "PKPG3N3MF2AKUFGWDKFG"
API_SECRET = "xhVMbvi3DJkoCWWeXNoYqC0FTWb9o7iST9ASzix8"
BASE_URL = "https://paper-api.alpaca.markets/"  # Paper trading URL

# Initialize API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL)
account = api.get_account()
portfolio_value = float(account.equity)

# Load market data
DATA_DIR = "market_data"
csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
stock_data = {os.path.splitext(os.path.basename(f))[0]: pd.read_csv(f) for f in csv_files}

# Compute ATR values
atr_values = {}
for stock, df in stock_data.items():
    if df.empty:
        continue

    df["TR"] = df[["high", "low", "close"]].max(axis=1) - df[["high", "low", "close"]].min(axis=1)
    df["ATR"] = df["TR"].rolling(14).mean()
    df.dropna(inplace=True)
    atr_values[stock] = df["ATR"].iloc[-1] if not df.empty else 0
    print(f"\n{stock} ATR Value: {atr_values[stock]:.2f}")

# Calculate position sizes
risk_per_trade = portfolio_value * 0.01
position_sizes = {
    stock: int(risk_per_trade / (df["close"].iloc[-1] - (df["close"].iloc[-1] - (atr_values[stock] * 2))))
    if (df["close"].iloc[-1] - (atr_values[stock] * 2)) > 0 else 0
    for stock, df in stock_data.items() if not df.empty
}

for stock, size in position_sizes.items():
    latest_price = stock_data[stock]["close"].iloc[-1]
    stop_loss = latest_price - (atr_values[stock] * 2)
    trade_risk = latest_price - stop_loss
    print(f"\n{stock} Position Size: {size} (Stop Loss: {stop_loss:.2f}, Trade Risk: {trade_risk:.2f})")

# Risk management check
starting_equity = float(account.last_equity)
daily_loss = (starting_equity - portfolio_value) / starting_equity
stop_trading = daily_loss > 0.05
