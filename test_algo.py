# from datetime import datetime, timedelta
# from SmartApi import SmartConnect  # Ensure SmartApi SDK is installed
# #
# # # Replace with actual API credentials
# API_KEY = "8x8RGK2s"
# CLIENT_CODE = "J263557"
# PASSWORD = "7753"
# #
# # # Initialize SmartConnect instance
# # smart = SmartConnect(api_key=API_KEY)
# # ltpSmart = SmartConnect(api_key="2dI4Pnr7")
# #
# #
# # def fetch_candle_data(smart, interval):
# #     """
# #     Fetch historical candle data directly without using a token object.
# #     """
# #     to_date = datetime.now()
# #     from_date = to_date - timedelta(minutes=480)
# #     from_date_format = from_date.strftime("%Y-%m-%d %H:%M")
# #     to_date_format = to_date.strftime("%Y-%m-%d %H:%M")
# #
# #
# #     historic_params = {
# #         "exchange": "NFO",  # Directly passing exchange
# #         "symboltoken": "37201",  # Directly passing symbol token
# #         "interval": interval,
# #         "fromdate": from_date_format,
# #         "todate": to_date_format,
# #     }
# #
# #     res_json = smart.getCandleData(historic_params)
# #     print("res_json res_json",res_json)
# #
# #     if "data" in res_json:
# #         data = res_json["data"][::-1]  # Reverse order if required
# #         return data
# #     else:
# #         return f"Error fetching candle data: {res_json}"
# #
# #
# # def fetch_ltp_data(ltpSmart, symbol, token_id):
# #     """
# #     Fetch LTP (Last Traded Price) data directly.
# #     """
# #     ltp_data = ltpSmart.ltpData("NFO", symbol, token_id)
# #
# #     return ltp_data
# #
# #
# # print("Fetching Candle Data...")
# # candle_data = fetch_candle_data(smart, "ONE_MINUTE")
# # print("Candle Data:",
# #       candle_data[:5] if isinstance(candle_data, list) else candle_data)  # Print first 5 entries for verification
# #
# #
# # # print("\nFetching LTP Data...")
# # # ltp_data = fetch_ltp_data(ltpSmart, "BANKNIFTY27FEB2544700CE", "37239")
# # # print("LTP Data:", ltp_data)
#
#
# # from_date_format = "2024-11-10 09:00"
# # to_date_format = "2024-11-13 09:16"
# from datetime import datetime, timedelta
# import os
# from getmac import get_mac_address
# import socket
# import pyotp
# import requests
#
#
# def get_jwt_token(api_key, client_code, password, token_code):
#     smart = SmartConnect(api_key=api_key)
#     data = smart.generateSession(
#         clientCode=client_code,
#         password=password,
#         totp=pyotp.TOTP(token_code).now()
#     )
#
#     # Decode the response to JSON
#     jwt_token = data.get('data', {}).get('jwtToken', None)
#     return jwt_token
#
#
# def fetch_candle_data(self, token, interval):
#     """
#     Simplified function to fetch Candle Data, generating local IP, public IP, and MAC address dynamically.
#     """
#     api_key = os.getenv("API_KEY")
#     client_code = os.getenv("CLIENT_CODE")
#     password = os.getenv("PASSWORD")
#     token_code = os.getenv("TOKEN_CODE")
#
#     try:
#         auth_token = get_jwt_token(api_key, client_code, password, token_code)
#         local_ip = socket.gethostbyname(socket.gethostname())  # Get local IP address
#         mac_address = get_mac_address()  # MAC address
#         to_date = datetime.now()
#
#         from_date = to_date - timedelta(minutes=2000)
#         from_date_format = from_date.strftime("%Y-%m-%d %H:%M")
#         to_date_format = to_date.strftime("%Y-%m-%d %H:%M")
#
#
# # Fetch public IP address
#         public_ip_response = requests.get("https://api.ipify.org?format=json")
#         public_ip_response.raise_for_status()
#         public_ip = public_ip_response.json().get("ip")
#
#         # Construct payload and headers
#         payload = {
#             "exchange": token.exch_seg,
#             "symboltoken": token.token_id,
#             "interval": interval,
#             "fromdate": from_date_format,
#             "todate": to_date_format
#         }
#         headers = {
#             "X-PrivateKey": api_key,
#             "Accept": "application/json",
#             "X-SourceID": "WEB",
#             "X-ClientLocalIP": local_ip,
#             "X-ClientPublicIP": public_ip,
#             "X-MACAddress": mac_address,
#             "X-UserType": "USER",
#             "Authorization": auth_token,
#             "Content-Type": "application/json"
#         }
#
#         # Make API request
#         response = requests.post(
#             "https://apiconnect.angelone.in/rest/secure/angelbroking/historical/v1/getCandleData",
#             json=payload,
#             headers=headers
#         )
#
#         # Check response status
#         # print("CANDLE DATA response", response.json())
#         response.raise_for_status()
#         return response.json()['data'][::-1]
#
#     except Exception as e:
#         raise Exception(f"Error fetching candle data: {str(e)}")


from SmartApi.smartConnect import SmartConnect
import pyotp
from datetime import datetime, timedelta
LTP_API_KEY = "ZlQnOy4h"
LTP_CLIENT_CODE = "S55329579"
LTP_PASSWORD = "4242"
LTP_TOKEN_CODE = "QRLYAZPZ6LMTH5AYILGTWWN26E"

API_KEY = "8x8RGK2s"
CLIENT_CODE = "J263557"
PASSWORD = "7753"
TOKEN_CODE = "3MYXRWJIJ2CZT6Y5PD2EU5RNNQ"
smart = SmartConnect(api_key=API_KEY)
ltp_smart = SmartConnect(api_key=LTP_API_KEY)
print(ltp_smart)
smart.generateSession(clientCode=CLIENT_CODE, password=PASSWORD, totp=pyotp.TOTP(TOKEN_CODE).now())
ltp_smart.generateSession(
            clientCode=LTP_CLIENT_CODE, password=LTP_PASSWORD, totp=pyotp.TOTP(LTP_TOKEN_CODE).now()
        )


def fetch_candle_data():
    to_date = datetime.now()
    from_date = to_date - timedelta(minutes=480)
    from_date_format = from_date.strftime("%Y-%m-%d %H:%M")
    to_date_format = to_date.strftime("%Y-%m-%d %H:%M")
    historic_params = {
        "exchange": "NFO",
        "symboltoken": "39954",
        "interval": "ONE_MINUTE",
        "fromdate": from_date_format,
        "todate": to_date_format,
    }

    res_json = smart.getCandleData(historic_params)
    print("resjson", res_json)
    data = res_json["data"][::-1]
    return data

def fetch_ltp_data():
    ltp_data = ltp_smart.ltpData(exchange="NFO", tradingsymbol="BANKNIFTY27FEB2549000CE", symboltoken="39954")
    return ltp_data
print(fetch_ltp_data())
fetch_candle_data()
