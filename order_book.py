# order_book.py

import threading
import heapq

class OrderBook:
    def __init__(self):
        # Heaps for bid and ask orders.
        # Bids use a max heap (store negative price) and asks a min heap.
        self.bids = []  # Each element: (-price, timestamp, order_id, order)
        self.asks = []  # Each element: (price, timestamp, order_id, order)
        self.orders = {}  # Map order_id -> order dictionary
        self.lock = threading.Lock()
        self.timestamp = 0  # To preserve insertion order for same-price orders

    def add_order(self, order):
        with self.lock:
            self.timestamp += 1
            order_id = order["OrderID"]
            price = float(order["Price"])
            side = order["Side"]
            order["timestamp"] = self.timestamp
            # Store order in dictionary for quick lookup.
            self.orders[order_id] = order

            if side == "B":
                heapq.heappush(self.bids, (-price, self.timestamp, order_id, order))
            elif side == "S":
                heapq.heappush(self.asks, (price, self.timestamp, order_id, order))
            else:
                print("Invalid order side:", side)

    def amend_order(self, order):
        # Amend by canceling the existing order and adding the updated one.
        order_id = order["OrderID"]
        with self.lock:
            if order_id in self.orders:
                self.cancel_order(order_id)
            self.add_order(order)

    def cancel_order(self, order_id):
        with self.lock:
            if order_id in self.orders:
                # Mark the order as cancelled. It will be cleaned from the heaps later.
                order = self.orders.pop(order_id)
                order["cancelled"] = True
            else:
                print("Order ID not found for cancellation:", order_id)

    def clean_heaps(self):
        # Remove cancelled orders from the top of the heaps.
        while self.bids and self.bids[0][3].get("cancelled", False):
            heapq.heappop(self.bids)
        while self.asks and self.asks[0][3].get("cancelled", False):
            heapq.heappop(self.asks)

    def get_best_bid(self):
        with self.lock:
            self.clean_heaps()
            return self.bids[0][3] if self.bids else None

    def get_best_ask(self):
        with self.lock:
            self.clean_heaps()
            return self.asks[0][3] if self.asks else None

    def update_order(self, order):
        action = order["Action"]
        if action == "A":
            self.add_order(order)
        elif action == "M":
            self.amend_order(order)
        elif action == "C":
            self.cancel_order(order["OrderID"])
        else:
            print("Unknown action:", action)

    def get_liquidity_signal(self, symbol):
        """
        Computes a liquidity signal for a given symbol.
        Sums the total quantity of non-cancelled buy and sell orders.
          Returns +1 if buy volume > sell volume,
          -1 if sell volume > buy volume,
           0 if equal.
        """
        with self.lock:
            total_bid = sum(
                float(o["Quantity"])
                for o in self.orders.values()
                if o["Symbol"] == symbol and o["Side"] == "B" and not o.get("cancelled", False)
            )
            total_ask = sum(
                float(o["Quantity"])
                for o in self.orders.values()
                if o["Symbol"] == symbol and o["Side"] == "S" and not o.get("cancelled", False)
            )
        if total_bid > total_ask:
            return 1
        elif total_ask > total_bid:
            return -1
        else:
            return 0
        
    def get_best_bid_for_symbol(self, symbol):
        """
        Returns the best (highest-priced) bid order for the given symbol
        across all exchanges.
        """
        with self.lock:
            valid_bids = [o for o in self.orders.values() 
                          if o["Symbol"] == symbol and o["Side"] == "B" and not o.get("cancelled", False)]
            if not valid_bids:
                return None
            # The best bid is the order with the maximum price.
            best_bid = max(valid_bids, key=lambda x: float(x["Price"]))
            return best_bid

    def get_best_ask_for_symbol(self, symbol):
        """
        Returns the best (lowest-priced) ask order for the given symbol
        across all exchanges.
        """
        with self.lock:
            valid_asks = [o for o in self.orders.values() 
                          if o["Symbol"] == symbol and o["Side"] == "S" and not o.get("cancelled", False)]
            if not valid_asks:
                return None
            # The best ask is the order with the minimum price.
            best_ask = min(valid_asks, key=lambda x: float(x["Price"]))
            return best_ask
