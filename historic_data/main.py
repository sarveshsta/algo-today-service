
from SmartApi import SmartConnect
from datetime import datetime, timedelta
import pyotp,time
import threading
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

obj = SmartConnect(api_key=api_key)
data = obj.generateSession(
    clientCode=client_code,
    password=password,
    totp=pyotp.TOTP(token_code).now()
)
#print(data)

AUTH_TOKEN="Bearer eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6IkoyNjM1NTciLCJyb2xlcyI6MCwidXNlcnR5cGUiOiJVU0VSIiwidG9rZW4iOiJleUpoYkdjaU9pSlNVekkxTmlJc0luUjVjQ0k2SWtwWFZDSjkuZXlKMWMyVnlYM1I1Y0dVaU9pSmpiR2xsYm5RaUxDSjBiMnRsYmw5MGVYQmxJam9pZEhKaFpHVmZZV05qWlhOelgzUnZhMlZ1SWl3aVoyMWZhV1FpT2pFeUxDSnpiM1Z5WTJVaU9pSXpJaXdpWkdWMmFXTmxYMmxrSWpvaU9UYzFNVEEzT0dZdFpXSmpaaTB6WXpJeUxUaGpPVE10WW1VME56azBOekZsTVdVM0lpd2lhMmxrSWpvaWRISmhaR1ZmYTJWNVgzWXhJaXdpYjIxdVpXMWhibUZuWlhKcFpDSTZNVElzSW5CeWIyUjFZM1J6SWpwN0ltUmxiV0YwSWpwN0luTjBZWFIxY3lJNkltRmpkR2wyWlNKOWZTd2lhWE56SWpvaWRISmhaR1ZmYkc5bmFXNWZjMlZ5ZG1salpTSXNJbk4xWWlJNklrb3lOak0xTlRjaUxDSmxlSEFpT2pFM01qYzROalUwTVRZc0ltNWlaaUk2TVRjeU56YzJOek01TWl3aWFXRjBJam94TnpJM056WTNNemt5TENKcWRHa2lPaUpsTXpFME5XWTVaQzFrTTJZMkxUUTFOVFF0WW1Vd1l5MW1NREZqWkdFeU5tRXlOV0VpZlEubGp6TzhJbVZiWVNhM25XZGE2YlBhLUZZNXdKNzVkODlvVk9iMkZCTWU2YXczZURtVXRPU0cxUW9zbnFFVTVDQjU4RllQQ3ZVaXlwdGhOSVJNVzZybGNidlVFc0F5MXlRelVPLTNpbFNNblE2X0g4QVcxd0YwUlBwZXF0S29BeGVUdFl3NDVKeWg0dmZqUGNoU0diNnUyTkY2V0pMWW1Kb19zNkZXUDBZbC1vIiwiQVBJLUtFWSI6IlQ0TUhWcFhIIiwiaWF0IjoxNzI3NzY3NDUyLCJleHAiOjE3Mjc4NjU0MTZ9.Yoj6QEwv_xOJZyNt8hSgiZ6mRSLqR1Vyx9n2-UVDUptDZjJgaNGv0CWWETFajxYW4pFIP-LPmFx5hgR-twkm2Q"
refreshtoken='eyJhbGciOiJIUzUxMiJ9.eyJ0b2tlbiI6IlJFRlJFU0gtVE9LRU4iLCJSRUZSRVNILVRPS0VOIjoiZXlKaGJHY2lPaUpTVXpJMU5pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SjFjMlZ5WDNSNWNHVWlPaUpqYkdsbGJuUWlMQ0owYjJ0bGJsOTBlWEJsSWpvaWRISmhaR1ZmY21WbWNtVnphRjkwYjJ0bGJpSXNJbWR0WDJsa0lqb3dMQ0prWlhacFkyVmZhV1FpT2lJNU56VXhNRGM0WmkxbFltTm1MVE5qTWpJdE9HTTVNeTFpWlRRM09UUTNNV1V4WlRjaUxDSnJhV1FpT2lKMGNtRmtaVjlyWlhsZmRqRWlMQ0p2Ylc1bGJXRnVZV2RsY21sa0lqb3dMQ0pwYzNNaU9pSnNiMmRwYmw5elpYSjJhV05sSWl3aWMzVmmw5elpYSjJhV05sSWl3aWMzVmlJam9pU2pJMk16VTFOeUlzSW1WNGNDSTZNVGN5TnprME1ETTJNU3dpYm1KbUlqb3hOekkzTnpZM05UQXhMQ0pwWVhRaU9qRTNNamMzTmpjMU1ERXNJbXAwYVNJNkltTm1OR1EzWkRJMUxUQXdOMk10TkdWalpTMDVZbVV3TFRoaFpEQmxZalF4WkRjNVlpSjkubHVHYnlMWGJRYUpRMXB1eFdlR2V4QlRNNHJiQU54S3dLTVhOd1N3ZUZNbnFGT3JSeWFiaU45ZC1wSlNGVWsxOFhkc2J4b05TV0F5ODcxTkwxMjZOVk0yWmpCXzBiWXo3REY1bDJPclBjZGtBemRJQU1UcHBoRV9GVXltU2o5T01WVkltXzB3V1NLLVg2T0wxNzZTSTJqR2x6Zk5uR000YnZYMzk3Z1JYM2ZvIiwiaWF0IjoxNzI3NzY3NTYxfQ.vgUcs9JkqfOxoCv8BJDlpCSGyzJIMDDn9A9rEuH9f63ZIp-kRuQipLc0qWBBoBsOeFJft5EcPQ6ayVYlHZeSaQ'
FEED_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6IlM1NTMyOTU3OSIsImlhdCI6MTcyNzY5NjIwOCwiZXhwIjoxNzI3NzgyNjA4fQ.0DAMPyFALFPY-hYBVvG6JX9xfUqZ8tjJIa4UMtXZRZNUdtCiL6BKMdCH0g6IWiFCT2u2m1snkt-bRVUe_H5Zag"
res=obj.getProfile(refreshtoken)

"""
    Created on Monday Feb 2 2022

    @author: Nishant Jain

    :copyright: (c) 2022 by Angel One Limited
"""

from smartWebSocketV2 import SmartWebSocketV2
import uuid
correlation_id = str(uuid.uuid4())
action = 0
mode = 1

token_list = [{"exchangeType": 2, "tokens": ["57445"]}]

sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, CLIENT_CODE, FEED_TOKEN)


def on_data(wsapp, message):
    print("Ticks: {}".format(message))


def on_open(wsapp):
    print("on open")
    sws.subscribe(correlation_id, mode, token_list)


def on_error(wsapp, error):
    print(error)


def on_close(wsapp):
    print("Close")


# Assign the callbacks.
sws.on_open = on_open
sws.on_data = on_data
sws.on_error = on_error
sws.on_close = on_close

#sws.connect()
threading.Thread(target=sws.connect()).start()
print("done")
time.sleep(10)
