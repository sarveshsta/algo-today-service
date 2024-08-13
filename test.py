from SmartApi import SmartConnect
from datetime import datetime
import pyotp

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
symbol = 'FINNIFTY13AUG2423200CE'
token = '44605'
def place_order(symbol, token, price, quantity):
    orderparams ={
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": "BUY",
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


def modify_order(self, variety, symbol, token, transaction, order_type, price, quantity):
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
            "quantity": quantity
        }
        orderId = smart.modifyOrder(orderparams)
        print("The order id is: {}".format(orderId))
        return orderId
    except Exception as e:
        print("Order modification failed: {}".format(e))
        return False


# def place_stoploss_limit_order(symbol, token, quantity, stoploss_price, limit_price):
#     stoploss_price = round(stoploss_price, 1)
#     limit_price = round(limit_price, 1)
#         # Validate parameters
#         if not symbol or not token or not quantity or not stoploss_price or not limit_price:
#             raise ValueError("Missing required parameters")

#         try:
#             quantity = int(quantity)
#         except ValueError:
#             raise ValueError("Quantity must be an integer")

#         try:
#             stoploss_price = float(stoploss_price)
#             limit_price = float(limit_price)
#         except ValueError:
#             raise ValueError("Stop-loss price and limit price must be numbers")

#         # Define stop-loss limit order parameters
#         stoploss_limit_order_params = {
#             "variety": "STOPLOSS",
#             "tradingsymbol": str(symbol),
#             "symboltoken": str(token),
#             "transactiontype": "SELL",  # Selling to trigger stop-loss
#             "exchange": "NFO",
#             "ordertype": "STOPLOSS_LIMIT",  # Stop-loss limit order
#             "producttype": "INTRADAY",
#             "duration": "DAY",
#             "price": str(limit_price),  # Limit price for SL-L orders
#             "triggerprice": str(stoploss_price),  # Trigger price for stop-loss
#             "quantity": str(quantity),
#         }


trade_book = smart.tradeBook()['data']
# print(trade_book)
for i in trade_book:
    if i['orderid'] == "240813101157567":
        print(i)

