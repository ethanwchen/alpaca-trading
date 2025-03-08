# decision_maker.py

def decision_maker(news_signal, liquidity_signal, mean_rev_signal, order_book, symbol, default_price):
    """
    Combine the three signals (news, liquidity, mean reversion).
      +1 = buy, -1 = sell, 0 = no signal
    If 2 or more signals say buy, we want to buy from the exchange offering the
    lowest ask for 'symbol'.
    If 2 or more signals say sell, we want to sell to the exchange offering the
    highest bid for 'symbol'.
    If no consensus, return None.

    'default_price' is the current observed price (in case we have no best bid/ask).
    """
    signals = [news_signal, liquidity_signal, mean_rev_signal]
    buy_votes = signals.count(1)
    sell_votes = signals.count(-1)

    if buy_votes >= 2:
        # We want to BUY at the best ask
        best_ask = order_book.get_best_ask_for_symbol(symbol)
        if best_ask is None:
            # No ask available, skip
            return None
        # Price is the best ask's price
        best_price = best_ask['price']
        best_exchange = best_ask.get('exchange', 'Unknown')
        # We can choose quantity. For simplicity, let's buy up to best_ask's quantity
        quantity = best_ask['quantity']

        return {
            "Symbol": symbol,
            "Exchange": best_exchange,
            "Quantity": str(quantity),
            "Side": "B",
            "Price": f"{best_price:.2f}",
            "Type": "MARKET"  # or LIMIT, depending on your logic
        }

    elif sell_votes >= 2:
        # We want to SELL at the best bid
        best_bid = order_book.get_best_bid_for_symbol(symbol)
        if best_bid is None:
            # No bid available, skip
            return None
        best_price = best_bid['price']
        best_exchange = best_bid.get('exchange', 'Unknown')
        quantity = best_bid['quantity']

        return {
            "Symbol": symbol,
            "Exchange": best_exchange,
            "Quantity": str(quantity),
            "Side": "S",
            "Price": f"{best_price:.2f}",
            "Type": "MARKET"
        }

    # No consensus
    return None
