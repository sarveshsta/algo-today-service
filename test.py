from SmartApi import SmartConnect
import pyotp
from datetime import datetime, timedelta

NFO_DATA_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
OPT_TYPE = "OPTIDX"
EXCH_TYPE = "NFO"

API_KEY = "T4MHVpXH"
CLIENT_CODE = "J263557"
PASSWORD = "7753"
TOKEN_CODE = "3MYXRWJIJ2CZT6Y5PD2EU5RNNQ"
TOTP = pyotp.TOTP(TOKEN_CODE).now()
print("TOTP", TOTP)


smart = SmartConnect(api_key=API_KEY)
data = smart.generateSession(
    clientCode=CLIENT_CODE,
    password=PASSWORD,
    totp=TOTP
)
print(data)
to_date = datetime.now()
from_date = to_date - timedelta(minutes=360)
from_date_format = from_date.strftime("%Y-%m-%d %H:%M")
to_date_format = to_date.strftime("%Y-%m-%d %H:%M")
historic_params = { 
            "exchange": "NFO",
            "symboltoken": "35781",
            "interval": "SIX_MINUTE",
            "fromdate": from_date_format,
            "todate": to_date_format,
        }
candle_data = smart.getCandleData(historicDataParams=historic_params)
print(candle_data)
