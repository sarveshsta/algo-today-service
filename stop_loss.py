def place_order(symbol, token, transaction, order_type, quantity, price="0"):
    try:
        orderparams = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": transaction,
            "exchange": "NFO",
            "ordertype": order_type,
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": "0" if order_type == "MARKET" else price,
            "squareoff": "0",
            "stoploss": "0",
            "quantity": quantity,
        }
        orderId = smart.placeOrder(orderparams)
        print("The order id is: {}".format(orderId))
        return orderId
    except Exception as e:
        print("Order placement failed: {}".format(e))
        return False
