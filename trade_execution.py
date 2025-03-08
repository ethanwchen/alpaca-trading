import alpaca_trade_api as tradeapi
import csv
import os
from trading_strategy import trade_signals
from risk_management import position_sizes, stop_trading

# Set API credentials
API_KEY = "PKPG3N3MF2AKUFGWDKFG"
API_SECRET = "xhVMbvi3DJkoCWWeXNoYqC0FTWb9o7iST9ASzix8"
BASE_URL = "https://paper-api.alpaca.markets/"  # Paper trading URL

# Initialize API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL)
LOG_FILE = "trade_log.csv"

# Ensure log file exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Stock", "Action", "Quantity"])

print("\nStarting Trade Execution...")

if stop_trading:
    print("Daily loss limit exceeded. Stopping trading.\n")
else:
    print("Daily loss is within limits. Proceeding with trade execution...\n")
    print("Trade Signals:", trade_signals)
    print("Position Sizes:", position_sizes)

    for stock, action in trade_signals.items():
        qty = position_sizes.get(stock, 0)

        if action in {"buy", "sell"} and qty > 0:
            print(f"Executing {action.upper()} order for {qty} shares of {stock}...")
            try:
                api.submit_order(
                    symbol=stock,
                    qty=qty,
                    side=action,
                    type="market",
                    time_in_force="gtc"
                )
                print(f"Order placed: {action.upper()} {qty} shares of {stock}\n")

                with open(LOG_FILE, "a", newline="") as f:
                    csv.writer(f).writerow([stock, action, qty])
            except Exception as e:
                print(f"Error executing trade for {stock}: {e}")

# Display trade log
print("\nTrade Log:")
with open(LOG_FILE, "r") as f:
    print(f.read() if os.stat(LOG_FILE).st_size > 0 else "No trades executed. Check signals & position sizes.")
