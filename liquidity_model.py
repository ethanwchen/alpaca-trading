def get_liquidity_signal(order_book, symbol):
    """
    Computes a liquidity signal for a given symbol:
      +1 if total buy volume > total sell volume,
      -1 if total sell volume > total buy volume,
       0 if they are equal or the symbol doesn't exist.
    """
    with order_book.lock:
        total_bid = 0
        total_ask = 0
        for order_id, ord_data in order_book.orders.items():
            if ord_data.get("cancelled", False):
                continue
            if ord_data["Symbol"] == symbol:
                side = ord_data["Side"]
                quantity = float(ord_data["Quantity"])
                if side == "B":
                    total_bid += quantity
                elif side == "S":
                    total_ask += quantity

    if total_bid > total_ask:
        return 1
    elif total_ask > total_bid:
        return -1
    else:
        return 0
