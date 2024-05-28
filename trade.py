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


# order_id = place_order("MIDCPNIFTY06MAY2410875PE", "36559", "BUY", "7.20", "75")
# print("The order ID that was returned is ", order_id)
OrderBook = smart.orderBook()['data']
print(OrderBook)
for i in OrderBook:
    if i['orderid'] == '240503000519204':
        print(i['text'])
# import requests
# # 240503000519204 240503000449810
# order_id = "240503000523710"
# url = f"https://apiconnect.angelbroking.com/rest/secure/angelbroking/order/v1/details/{order_id}"

# r = requests.post(url)
# # print(r.json())


