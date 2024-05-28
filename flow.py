import requests, pyotp
from SmartApi import SmartConnect
API_KEY = "T4MHVpXH"
CLIENT_CODE = "J263557"
PASSWORD = "7753"
TOKEN_CODE = "3MYXRWJIJ2CZT6Y5PD2EU5RNNQ"

LTP_API_KEY = "MolOSZTR"
LTP_CLIENT_CODE = "S55329579"
LTP_PASSWORD = "4242"
LTP_TOKEN_CODE = "QRLYAZPZ6LMTH5AYILGTWWN26E"

base_url = "https://apiconnect.angelbroking.com"
# smart = SmartConnect(api_key=API_KEY)
# data = smart.generateSession(
#     clientCode=CLIENT_CODE,
#     password=PASSWORD,
#     totp=pyotp.TOTP(TOKEN_CODE).now()
# )
# print(data)

# def login():
#     url = base_url + "/rest/auth/angelbroking/user/v1/loginByPassword"
#     headers = {
#     'Content-Type': 'application/json',
#     'Accept': 'application/json',
#     'X-UserType': 'USER',
#     'X-SourceID': 'WEB',
#     'X-ClientLocalIP': '106.193.147.98',
#     'X-ClientPublicIP': '127.0.0.1',
#     'X-MACAddress': 'MAC_ADDRESS',
#   }
#     payload = {"clientcode":LTP_CLIENT_CODE,"password":LTP_PASSWORD,
#                "totp":pyotp.TOTP(LTP_TOKEN_CODE).now()}
#     r = requests.post(url, json=payload, headers=headers)
#     print(r.json())
#     if r.json()['success']:return r.json()['data']['jwtToken']
#     else: return False
# if login():
#   jwt_token = login()
# else: exit()

# jwt_token = data['data']['jwtToken']
jwt_token = """Bearer eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6IkoyNjM1NTciLCJyb2xlcyI6MCwidXNlcnR5cGUiOiJVU0VSIiwidG9rZW4iOiJleUpoYkdjaU9pSklVelV4TWlJc0luUjVjQ0k2SWtwWFZDSjkuZXlKemRXSWlPaUpLTWpZek5UVTNJaXdpWlhod0lqb3hOekUwT0RBNE5qQTVMQ0pwWVhRaU9qRTNNVFEzTWpBeU1qVXNJbXAwYVNJNklqQTFZV1JrWW1VeUxURXhaVFl0TkRVd015MWhaalppTFdVNE5qVmhaalUxWmpReE1TSXNJbTl0Ym1WdFlXNWhaMlZ5YVdRaU9qY3NJbk52ZFhKalpXbGtJam9pTXlJc0luVnpaWEpmZEhsd1pTSTZJbU5zYVdWdWRDSXNJblJ2YTJWdVgzUjVjR1VpT2lKMGNtRmtaVjloWTJObGMzTmZkRzlyWlc0aUxDSm5iVjlwWkNJNk55d2ljMjkxY21ObElqb2lNeUlzSW1SbGRtbGpaVjlwWkNJNklqazNOVEV3TnpobUxXVmlZMll0TTJNeU1pMDRZemt6TFdKbE5EYzVORGN4WlRGbE55SXNJbUZqZENJNmUzMTkuSE1MTkg0dWhJeFdyV1BNejBSY2NyRW1rOHlXMkUzUHBuRE1xbWp6Q0xoZmlWOEs4OG81N3UxRTRjSWI3blZ6eF9WWFBuVWhRdUh6QjRub2VqX3ZITVEiLCJBUEktS0VZIjoiVDRNSFZwWEgiLCJpYXQiOjE3MTQ3MjAyODUsImV4cCI6MTcxNDgwODYwOX0.QoHJbhzxz_4RlXOWY7SZD8BqVs-jvM_jR2_7p3Fe1GuKCT6M8BTe0-ctfrdZUtPE-tf8HFkWBdCej36KU0gsGg"""

# def place_order(symbol, token, transaction, price):
#     url = base_url + "/rest/secure/angelbroking/order/v1/placeOrder"
#     orderparams ={
#             "variety": "NORMAL",
#             "tradingsymbol": symbol,
#             "symboltoken": token,
#             "transactiontype": transaction,
#             "exchange": "NFO",
#             "ordertype": "MARKET",
#             "producttype": "INTRADAY",
#             "duration": "DAY",
#             "price": price,
#             "squareoff": "0",
#             "stoploss": "0",
#             "quantity": 75
#         }
#     headers = {
#       'Authorization': jwt_token,
#       'Content-Type': 'application/json',
#       'Accept': 'application/json',
#       'X-UserType': 'USER',
#       'X-SourceID': 'WEB',
#       'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
#       'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
#       'X-MACAddress': 'MAC_ADDRESS',
#       'X-PrivateKey': 'T4MHVpXH'
#     }
#     r = requests.post(url, json=orderparams, headers=headers)
#     print(r.text)
#     print(r.json())

# place_order("NIFTY09MAY2422400CE", "46925", "80", "BUY") 
import requests
headers = {
  'X-PrivateKey': API_KEY,
  'Accept': 'application/json',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-UserType': 'USER',
  'Authorization': jwt_token,
  'Accept': 'application/json',
  'X-SourceID': 'WEB',
  'Content-Type': 'application/json'
}

req = requests.get(url='https://apiconnect.angelbroking.com/rest/secure/angelbroking/order/v1/details/05ebf91b-bea4-4a1d-b0f2-4259606570e3')

print(req.json())
