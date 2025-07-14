import os
import pyotp
from fastapi import APIRouter
from threading import Thread
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from .websocket_provider import (
    smart, ltp_smart, LIVE_FEED_JSON,
    WebSocketEnabledDataProvider, connectFeed
)
from .strategy_runner import strategy_worker
from .strategy_state import start_strategy_flag, register_thread, stop_strategy_flag
from .instrument_utils import get_instruments_from_openapi
from .schema import StrategyStartInput  # adjust import based on your project


router = APIRouter()

@router.post("/run-strategy")
async def run_strategy(payload: StrategyStartInput):
    # 1. Start strategy flag
    start_strategy_flag(payload.strategy_id)

    # 2. Get instrument token
    symbol = f"{payload.index}{payload.expiry}{payload.strike_price}{payload.option_type}"
    instruments = get_instruments_from_openapi(os.getenv("NFO_DATA_URL"), [symbol])

    if not instruments:
        return {"message": f"Instrument {symbol} not found", "success": False}

    token = instruments[0]["token"]
    token_int = int(token)

    # 3. Authenticate and create WebSocket connection
    CLIENT_CODE = os.getenv("CLIENT_CODE")
    PASSWORD = os.getenv("PASSWORD")
    TOKEN_CODE = os.getenv("TOKEN_CODE")
    totp = pyotp.TOTP(TOKEN_CODE).now()

    session = smart.generateSession(CLIENT_CODE, PASSWORD, totp)
    feed_token = session["data"]["feedToken"]
    jwt_token = session["data"]["jwtToken"]

    # 4. Set up and connect SmartWebSocket
    sws = SmartWebSocketV2(jwt_token, os.getenv("API_KEY"), CLIENT_CODE, feed_token)
    connectFeed(sws, [token_int])  # subscribe to this token

    # 5. Prepare live LTP provider
    ltp_provider = WebSocketEnabledDataProvider(smart, ltp_smart, LIVE_FEED_JSON)

    # 6. Start strategy thread with LTP provider
    thread = Thread(
        target=strategy_worker,
        args=(payload.dict(), ltp_provider),
        daemon=True
    )
    thread.start()
    register_thread(payload.strategy_id, thread)

    return {"message": f"Strategy {payload.strategy_id} started.", "success": True}


@router.post("/stop-strategy")
async def stop_strategy(strategy_id: str):
    stop_strategy_flag(strategy_id)
    return {"message": f"Strategy {strategy_id} stop signal sent."}