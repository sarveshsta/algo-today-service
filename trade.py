from datetime import datetime

import pyotp
from SmartApi import SmartConnect

NFO_DATA_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
OPT_TYPE = "OPTIDX"
EXCH_TYPE = "NFO"

API_KEY = "T4MHVpXH"
CLIENT_CODE = "J263557"
PASSWORD = "7753"
TOKEN_CODE = "3MYXRWJIJ2CZT6Y5PD2EU5RNNQ"

LTP_API_KEY = "MolOSZTR"
LTP_CLIENT_CODE = "S55329579"
LTP_PASSWORD = "4242"
LTP_TOKEN_CODE = "QRLYAZPZ6LMTH5AYILGTWWN26E"


api_key = API_KEY
token_code = TOKEN_CODE
client_code = CLIENT_CODE
password = PASSWORD
ltp_api_key = LTP_API_KEY

smart = SmartConnect(api_key=api_key)
data = smart.generateSession(
    clientCode=client_code,
    password=password,
    totp=pyotp.TOTP(token_code).now()
)

ltp_smart = SmartConnect(api_key=LTP_API_KEY)
ltp_data = ltp_smart.generateSession(
    clientCode=LTP_CLIENT_CODE,
    password=LTP_PASSWORD,
    totp=pyotp.TOTP(LTP_TOKEN_CODE).now()
)

symbol = "NIFTY25JUL2423500PE"
token = "65232"
quantity = "25"
stoploss_price = "1.0"  # Trigger price
limit_price = "1.0"  

def place_order(symbol, token, transaction, price, quantity):
    try:
        orderparams ={
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": transaction,
            "exchange": "NFO",
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": price,
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


def modify_order(self, symbol, token, transaction, price, quantity):
    try:
        orderparams ={
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": transaction,
            "exchange": "NFO",
            "ordertype": "STOPLOSS",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": "0",
            "squareoff": "0",
            "stoploss": "2",
            "quantity": quantity
        }
        orderId = smart.modifyOrder(orderparams)
        print("The order id is: {}".format(orderId))
        return orderId
    except Exception as e:
        print("Order modification failed: {}".format(e))
        return False


# order_id = place_order(symbol, token, "BUY", "0", "25")
order_id = "240724100911923"


def get_order_details(order_id):
    try:
        order_book = smart.orderBook().get('data', [])
        for order in order_book:
            if order['orderid'] == order_id:
                return order
        print(f"No order found with ID {order_id}")
        return None
    except Exception as e:
        print(f"Failed to fetch order details: {e}")
        return None

def place_stoploss_limit_order(symbol, token, quantity, stoploss_price, limit_price):
    try:
        # Validate parameters
        if not symbol or not token or not quantity or not stoploss_price or not limit_price:
            raise ValueError("Missing required parameters")

        try:
            quantity = int(quantity)
        except ValueError:
            raise ValueError("Quantity must be an integer")

        try:
            stoploss_price = float(stoploss_price)
            limit_price = float(limit_price)
        except ValueError:
            raise ValueError("Stop-loss price and limit price must be numbers")

        # Define stop-loss limit order parameters
        stoploss_limit_order_params = {
            "variety": "STOPLOSS",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": "SELL",  # Selling to trigger stop-loss
            "exchange": "NFO",
            "ordertype": "STOPLOSS_LIMIT",  # Stop-loss limit order
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": str(limit_price),  # Limit price for SL-L orders
            "triggerprice": str(stoploss_price),  # Trigger price for stop-loss
            "quantity": str(quantity),
        }

        # Place the stop-loss limit order
        response = smart.placeOrder(stoploss_limit_order_params)
        
        if not response:
            raise ValueError("Received empty response from server")
        
        # Check if the response contains order ID or error message
        order_id = response
        if order_id:
            print(f"Stop-loss limit order placed successfully. Order ID: {order_id}")
            return order_id
        else:
            error_message = response.get("text", "Unknown error")
            raise ValueError(f"Failed to place stop-loss limit order: {error_message}")

    except Exception as e:
        print(f"Stop-loss limit order placement failed: {e}")
        return False
# 240724100911923 wit stop loss
# 240724100891970 initial order placed

def modify_stoploss_limit_order(symbol, token, quantity, stoploss_price, limit_price, order_id):
    try:
        if not symbol or not token or not quantity or not stoploss_price or not limit_price:
            raise ValueError("Missing required parameters")

        try:
            quantity = int(quantity)
        except ValueError:
            raise ValueError("Quantity must be an integer")

        try:
            stoploss_price = float(stoploss_price)
            limit_price = float(limit_price)
        except ValueError:
            raise ValueError("Stop-loss price and limit price must be numbers")

        stoploss_limit_order_params = {
            "variety": "STOPLOSS",
            "orderid": order_id,
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": "SELL",  # Selling to trigger stop-loss
            "exchange": "NFO",
            "ordertype": "STOPLOSS_LIMIT",  # Stop-loss limit order
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": str(limit_price),  # Limit price for SL-L orders
            "triggerprice": str(stoploss_price),  # Trigger price for stop-loss
            "quantity": str(quantity),
        }

        # Place the stop-loss limit order
        response = smart.modifyOrder(stoploss_limit_order_params)
        
        if not response:
            raise ValueError("Received empty response from server")
        
        # Check if the response contains order ID or error message
        order_id = response
        if order_id:
            print(f"Stop-loss limit order modified successfully. Order ID: {order_id}")
            return order_id
        else:
            raise ValueError(f"Failed to modify stop-loss limit order: {order_id}")

    except Exception as e:
        print(f"Stop-loss limit order modified failed: {e}")
        return False

# order_id = place_stoploss_limit_order(symbol, token, quantity, stoploss_price, limit_price)

order_id = modify_stoploss_limit_order(symbol, token, quantity, stoploss_price, limit_price, "240724100911923")

