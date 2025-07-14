# websocket_provider.py
import os
import json
import threading
from datetime import datetime
from time import sleep
import logging
from SmartApi.smartConnect import SmartConnect


LIVE_FEED_JSON = {}

API_KEY = os.getenv("API_KEY")
CLIENT_CODE = os.getenv("CLIENT_CODE")
PASSWORD = os.getenv("PASSWORD")
TOKEN_CODE = os.getenv("TOKEN_CODE")
NFO_DATA_URL = os.getenv("NFO_DATA_URL")
CORRELATION_ID = "jahsgfhjaf2"
FEED_MODE = 1

smart = SmartConnect(api_key=API_KEY)
ltp_smart = SmartConnect(api_key=API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketEnabledDataProvider:
    def __init__(self, smart, ltpSmart, live_feed_data: dict):
        self.__smart = smart
        self.__ltpSmart = ltpSmart
        self.__live_feed_data = live_feed_data
        
    def fetch_ltp_data(self, token):
        try:
            token_id = token.token  # ✅ attribute access
            symbol = token.symbol   # ✅ attribute access

            if token_id in self.__live_feed_data and 'ltp' in self.__live_feed_data[token_id]:
                ltp = self.__live_feed_data[token_id]['ltp']
                logger.info(f"WebSocket LTP for {symbol}: {ltp}")
                return ltp

            logger.info(f"No WebSocket LTP for {symbol}. Fallback to API")
            ltp_data = self.__ltpSmart.ltpData("NFO", symbol, token_id)
            sleep(0.5)

            if not ltp_data or 'data' not in ltp_data or 'ltp' not in ltp_data['data']:
                raise ValueError("Invalid LTP response")

            return ltp_data['data']['ltp']
        except Exception as e:
            logger.error(f"LTP error: {e}")
            raise ValueError(f"Failed to fetch LTP: {e}")


def on_data(wsapp, msg):
    try:
        if isinstance(msg, str):
            msg = json.loads(msg)

        token = msg.get('token')
        if not token:
            return

        ltp = msg.get('last_traded_price', 0) / 100.0
        LIVE_FEED_JSON[token] = {
            'token': token,
            'ltp': ltp,
            'timestamp': datetime.now().isoformat(),
            'raw_data': msg
        }
    except Exception as e:
        logger.error(f"WebSocket data error: {e}")

def on_error(wsapp, error):
    logger.error(f"WebSocket error: {error}")

def on_close(wsapp, status, reason):
    logger.info(f"WebSocket closed: {status} → {reason}")

def close_connection(sws):
    sws.max_retry_attempt = 0
    sws.close_connection()

def connectFeed(sws, token_list=None):
    def on_open(wsapp):
        logger.info("WebSocket opened")
        if token_list:
            payload = [{"exchangeType": 2, "tokens": token_list}]
            logger.info(f"Subscribing: {payload}")
            sws.subscribe(CORRELATION_ID, FEED_MODE, payload)

    sws.on_open = on_open
    sws.on_data = on_data
    sws.on_error = on_error
    sws.on_close = on_close

    threading.Thread(target=sws.connect, daemon=True).start()
