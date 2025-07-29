import os

from requests import session
import pyotp
from fastapi import APIRouter, Depends
from threading import Thread
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from .websocket_provider import (
    smart, ltp_smart, LIVE_FEED_JSON,
    WebSocketEnabledDataProvider, connectFeed
)
from .strategy_runner import strategy_worker
from .strategy_state import start_strategy_flag, register_thread, stop_strategy_flag, is_running
from .instrument_utils import get_instruments_from_openapi
from .schema import StrategyStartInput  # adjust import based on your project
from middlewares.auth_middleware import verify_token
from config.database.config import get_db
from .utils import get_user_credentials,SmartAPIService, get_smartapi_connection
from SmartApi.smartConnect import SmartConnect

router = APIRouter()

# @router.post("/run-strategy")
# async def run_strategy(payload: StrategyStartInput, user_data: dict = Depends(verify_token), db: session = Depends(get_db)):
#     # 1. Start strategy flag
#     print(user_data, "user_data")
#     start_strategy_flag(payload.strategy_id)

#     # 2. Get instrument token
#     symbol = f"{payload.index}{payload.expiry}{payload.strike_price}{payload.option_type}"
#     instruments = get_instruments_from_openapi(os.getenv("NFO_DATA_URL"), [symbol])

#     if not instruments:
#         return {"message": f"Instrument {symbol} not found", "success": False}

#     token = instruments[0]["token"]
#     token_int = int(token)
#     credentials = get_user_credentials(db,user_data['user_id'])
#     # 3. Authenticate and create WebSocket connection
#     totp = pyotp.TOTP(credentials['totp_secret']).now()
#     smart_connect_obj = SmartConnect(api_key=credentials['api_key'])
#     session = smart_connect_obj.generateSession(credentials['client_code'], credentials['password'], totp)
#     feed_token = session["data"]["feedToken"]
#     jwt_token = session["data"]["jwtToken"]

#     # 4. Set up and connect SmartWebSocket
#     sws = SmartWebSocketV2(jwt_token, credentials['api_key'], credentials['client_code'], feed_token)
#     connectFeed(sws, [token_int])  # subscribe to this token

#     # 5. Prepare live LTP provider
#     ltp_provider = WebSocketEnabledDataProvider(smart, ltp_smart, LIVE_FEED_JSON)

#     # 6. Start strategy thread with LTP provider
#     smart_client = get_smartapi_connection(credentials)
#     service = SmartAPIService(smart_client) 
#     thread = Thread(
#         target=strategy_worker,
#         args=(payload.dict(), ltp_provider, credentials, service, user_data),
#         daemon=True
#     )
#     thread.start()
#     register_thread(payload.strategy_id, thread)

#     return {"message": f"Strategy {payload.strategy_id} started.", "success": True}
from SmartApi.smartConnect import SmartConnect
from SmartApi.smartExceptions import DataException
import pyotp
from fastapi import HTTPException

@router.post("/run-strategy")
async def run_strategy(payload: StrategyStartInput, user_data: dict = Depends(verify_token), db: session = Depends(get_db)):
    print("📥 Strategy payload received:", payload.dict())
    print("🔐 Authenticated user:", user_data)

    start_strategy_flag(payload.strategy_id)

    symbol = f"{payload.index}{payload.expiry}{payload.strike_price}{payload.option_type}"
    print(f"🔍 Looking for instrument: {symbol}")
    instruments = get_instruments_from_openapi(os.getenv("NFO_DATA_URL"), [symbol])

    if not instruments:
        return {"message": f"❌ Instrument {symbol} not found", "success": False}

    token = instruments[0]["token"]
    token_int = int(token)
    print(f"📦 Token found: {token_int}")

    credentials = get_user_credentials(db, user_data['user_id'])
    totp = pyotp.TOTP(credentials['totp_secret']).now()

    try:
        print("🔐 Generating SmartAPI session...")
        smart_connect_obj = SmartConnect(api_key=credentials['api_key'])
        session = smart_connect_obj.generateSession(credentials['client_code'], credentials['password'], totp)
        feed_token = session["data"]["feedToken"]
        jwt_token = session["data"]["jwtToken"]

        print("📡 Connecting to SmartWebSocket...")
        sws = SmartWebSocketV2(jwt_token, credentials['api_key'], credentials['client_code'], feed_token)
        connectFeed(sws, [token_int])  # subscribe to this token

    except DataException as de:
        print(f"🚫 Rate limit or SmartAPI error: {de}")
        return {"message": f"Rate limit or authentication error: {de}", "success": False}
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {"message": f"Failed to initialize SmartAPI connection: {e}", "success": False}

    print("⚙️ Setting up LTP provider...")
    ltp_provider = WebSocketEnabledDataProvider(smart, ltp_smart, LIVE_FEED_JSON)

    print("🚀 Starting strategy thread...")
    # smart_client = get_smartapi_connection(credentials)
    service = SmartAPIService(smart_connect_obj)

    thread = Thread(
        target=strategy_worker,
        args=(payload.dict(), ltp_provider, credentials, service, user_data),
        daemon=True
    )
    thread.start()
    register_thread(payload.strategy_id, thread)

    return {"message": f"✅ Strategy {payload.strategy_id} started.", "success": True}


@router.post("/stop-strategy")
async def stop_strategy(strategy_id: str):
    stop_strategy_flag(strategy_id)
    return {"success": True,"message": f"Strategy {strategy_id} stop signal sent."}

@router.post("/strategy-status")
async def strategy_status(strategy_id: str):
    status = is_running(strategy_id)
    message = (
        f"Strategy {strategy_id} is currently running."
        if status else
        f"Strategy {strategy_id} is not running."
    )
    return {
        "strategy_id": strategy_id,
        "is_running": status,
        "message": message
    }