from SmartApi import SmartConnect
from datetime import datetime, timedelta
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



def fetch_candle_data( ):
 #   to_date = datetime.now()
    from_date = datetime.now() - timedelta(minutes=360)
    from_date_format = from_date.strftime("%Y-%m-%d %H:%M")
    to_date_format = datetime.now().strftime("%Y-%m-%d %H:%M")
    print("FrOM", from_date_format)
    print("To-datae", to_date_format)
    historic_params = {
        "exchange": "NFO",
        "symboltoken": "44133",
        "interval": "ONE_MINUTE",
        "fromdate": from_date_format,
        "todate": to_date_format,
    }
    print(smart)
    res_json = smart.getCandleData(historic_params)
    data = res_json["data"][::-1]
    print("Length ", len(data))
    return data

fetch_candle_data()

# def place_order(symbol, token, price, quantity):
#     orderparams ={
#             "variety": "NORMAL",
#             "tradingsymbol": symbol,
#             "symboltoken": token,
#             "transactiontype": "BUY",
#             "exchange": "NFO",
#             "ordertype": "MARKET",
#             "producttype": "INTRADAY",
#             "duration": "DAY",
#             "price": price,
#             "squareoff": "0",
#             "stoploss": "0",
#             "quantity": quantity,
#         }
#     orderId = smart.placeOrder(orderparams)
#     print("The order id is: {}".format(orderId))
#     return orderId


# def modify_order(symbol, token, quantity, stoploss_price, limit_price):
#     try:
#         orderparams ={
#             "variety": "NORMAL",
#             "tradingsymbol": symbol,
#             "orderid":"240813100563311",
#             "ordertype":"LIMIT",
#             "symboltoken": token,
#             "transactiontype": "SELL",
#             "exchange": "NFO",
#             "ordertype": "MARKET",
#             "producttype": "INTRADAY",
#             "duration": "DAY",
#             "price": str(limit_price),
#             "triggerprice": str(stoploss_price),  # Trigger price for stop-loss
#             "squareoff": "0",
#             "stoploss": "0",
#             "quantity": quantity
#         }
#         orderId = smart.modifyOrder(orderparams)
#         print("The order id is: {}".format(orderId))
#         return orderId
#     except Exception as e:
#         print("Order modification failed: {}".format(e))
#         return False


# def place_stoploss_limit_order(symbol, token, quantity, stoploss_price, limit_price):
#     stoploss_price = round(stoploss_price, 1)
#     limit_price = round(limit_price, 1)
#     try:
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
#         order_id = smart.placeOrder(stoploss_limit_order_params)

#         # Method 2: Place an order and return the full response
#         order_book = smart.orderBook()['data']
#         for i in order_book:
#             if i['orderid'] == order_id:
#                 return order_id, i
#         return order_id, None    
#     except Exception as e:
#         print(f"Failed stoploss place order, reason {e}")


# def modify_order_new_function(symbol, token, stoploss_price, limit_price, order_id, quantity):
#     modify_order = {
#             "orderid": str(order_id),
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
#     # Modify the order
#     response = smart.modifyOrder(modify_order)

#     # Check the response
#     if response['status'] == "success":
#         print(f"Order modified successfully. Order ID: {response['data']['orderid']}")
#     else:
#         print(f"Failed to modify the order. Error: {response['message']}")

# order_id = modify_order_new_function(symbol, token, 0.50, 0.40, "240813100563311", "25")
# print("SL placed", order_id)

# def some(order_id):
#     while True:
#         try:
#             order_book = smart.orderBook()['data'] 
#             order_book = smart.tradeBook()['data']
           
#             for i in order_book:
#                 if i['orderid'] == order_id:
#                     return i, order_id
#         except Exception as e:
#             print("error", e)
        
# some("240822101183262")

