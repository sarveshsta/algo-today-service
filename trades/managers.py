import requests
import asyncio
from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Dict, List
from config.constants import EXCH_TYPE, NFO_DATA_URL, OPT_TYPE
from config.database.config import get_db
from trades.models import TokenModel, Order
from fastapi import HTTPException
from trades.strategy.optimization import BaseStrategy, MultiIndexStrategy, OpenApiInstrumentReader, SmartApiDataProvider
from SmartApi import SmartConnect

tasks: Dict[str, asyncio.Task] = {}


def get_tokens(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    tokens = db.query(TokenModel).offset(skip).limit(limit).all()
    return tokens


def delete_all_tokens(db: Session = Depends(get_db)):
    db.query(TokenModel).delete()
    db.commit()
    return True


def fetch_tokens(db: Session = Depends(get_db)):
    url = NFO_DATA_URL
    response = requests.get(url, timeout=7)
    data = response.json()

    for instrument in data:
        st1 = instrument["exch_seg"] == EXCH_TYPE
        st2 = instrument["instrumenttype"] == OPT_TYPE
        if st1 and st2:
            db_token = TokenModel(**instrument)
            db.add(db_token)
            db.commit()


def retrieve_token(symbol: str, db: Session = Depends(get_db)):
    token = db.query(TokenModel).filter(TokenModel.symbol == symbol).first()
    if token:
        return token
    return None


def retrieve_expiry(index: str, db: Session = Depends(get_db)):
    indexes = db.query(TokenModel).filter(TokenModel.name == index).all()

    if indexes:
        response_list = [{"name": ind.name, "symbol": ind.symbol, "expiry": str(ind.expiry_date)} for ind in indexes]
        # print(response_list)
        return response_list
    return None


def retrieve_strike_price(index: str, expiry: str, db: Session = Depends(get_db)):
    indexes = db.query(TokenModel).filter(TokenModel.name == index, TokenModel.expiry_date == expiry).all()
    print(indexes)
    if indexes:
        response_list = [{"name": ind.name, "symbol": ind.symbol, "expiry": str(ind.expiry_date), "strike_price": ind.strike} for ind in indexes]
        # print(response_list)
        return response_list
    return None
    
    
def fetch_previous_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    print(orders)
    if orders:
        response_list = [{
            "order_id": order.order_id,
            "unique_order_id": order.unique_order_id,
            "token": order.token,
            "signal": order.signal,
            "price": order.price,
            "status": order.status,
            "quantity": order.quantity,
            "ordertype": order.ordertype,
            "producttype": order.producttype,
            "duration": order.duration,
            "stoploss": order.stoploss,
            "transactiontime": order.transactiontime
        }
            for order in orders]
        return response_list
    return None

async def strategy_start(strategy_id: str, index_and_candle_durations: dict, quantity_index: dict):
    smart = SmartConnect(api_key=api_key)
    ltp_smart = SmartConnect(api_key=LTP_API_KEY)


    ltp_smart.generateSession(
        clientCode=LTP_CLIENT_CODE, password=LTP_PASSWORD, totp=pyotp.TOTP(LTP_TOKEN_CODE).now()
    )

    try:
        smart.generateSession(clientCode=client_code, password=password, totp=pyotp.TOTP(token_code).now())
    except Exception as e:
        return {"message": str(e), "success": True}

    instrument_reader = OpenApiInstrumentReader(NFO_DATA_URL, list(index_and_candle_durations.keys()))
    smart_api_provider = SmartApiDataProvider(smart, ltp_smart)
    max_transactions_indicator = MultiIndexStrategy()
    strategy = BaseStrategy(instrument_reader, smart_api_provider, max_transactions_indicator, index_and_candle_durations, quantity_index)
    task = asyncio.create_task(strategy.run(), name=strategy_id)
    # await save_strategy(strategy_params)
    tasks[strategy_id] = task
    return task

async def strategy_stop(strategy_id: str):
    try:
        if strategy_id not in tasks:
            raise HTTPException(status_code=400, detail="Strategy not found")
        task_info = tasks[strategy_id]
        task_info.cancel()
        await task_info
    except asyncio.CancelledError:
        del tasks[strategy_id]
        raise HTTPException(status_code=200, detail="Strategy Stop")

    del tasks[strategy_id]

