from SmartApi.smartConnect import SmartConnect
import pandas as pd
from datetime import datetime, timedelta
import pytz
import pyotp
from dotenv import load_dotenv
import os
from .instrument_utils import get_instruments_from_openapi
from typing import List, Dict

load_dotenv()
EXCHANGE_MAP = {"NSE": "NSE", "NFO": "NFO"}

# SmartAPI credentials from .env
API_KEY = os.getenv("API_KEY")
CLIENT_CODE = os.getenv("CLIENT_CODE")
PASSWORD = os.getenv("PASSWORD")
TOKEN_CODE = os.getenv("TOKEN_CODE")
NFO_DATA_URL = os.getenv("NFO_DATA_URL")

def get_smartapi_connection():
    obj = SmartConnect(api_key=API_KEY)
    totp = pyotp.TOTP(TOKEN_CODE).now()
    data = obj.generateSession(CLIENT_CODE, PASSWORD, totp)
    return obj


# Fetch candle data
def get_candle_data(token: List[str], exchange: str, interval: str = "FIVE_MINUTE", days: int = 1):
    try:
        smartapi = get_smartapi_connection()
        ist = pytz.timezone('Asia/Kolkata')
        to_date = datetime.now(ist)
        from_date = to_date - timedelta(days=days)

        params = {
            "exchange": EXCHANGE_MAP[exchange],
            "symboltoken": get_instruments_from_openapi(NFO_DATA_URL, token)[0]['token'],
            "interval": interval, 
            "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
            "todate": to_date.strftime("%Y-%m-%d %H:%M")
        }

        response = smartapi.getCandleData(params)
        candles = response['data']
        df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df

    except Exception as e:
        print("Error fetching candles:", str(e))
        return pd.DataFrame()




