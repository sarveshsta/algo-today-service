from typing import List

import fastapi
from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload

from config.database.config import get_db
from trades.managers import *
from trades.models import TradeDetails, TradingData, StrategyValue
from trades.schema import (
    ExpirySchema,
    Order,
    TokenSchema,
    TradeDetailSchema,
    TradeDetailsSchema,
    TradingDataCreate,
    TradingDataResponse,
    TradingDataUpdate,
    StrategyDetailsSchema
)

router = fastapi.APIRouter()


@router.get("/", response_model=List[TokenSchema])
async def read_tokens(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tokens = get_tokens(db, skip=skip, limit=limit)
    return tokens


@router.delete("/")
def delete_tokens(db: Session = Depends(get_db)):
    delete_all_tokens(db)
    return JSONResponse({"success": True}, status_code=200)


@router.post("/")
def create_index_tokens(db: Session = Depends(get_db)):
    fetch_tokens(db)
    return JSONResponse({"success": True}, status_code=201)


@router.get('/trades_details/', response_model=List[TradeDetailSchema])
async def get_trade_details(db: Session = Depends(get_db)):
    # Fetch all trades and their related tokens using joinedload
    trades = db.query(TradeDetails).options(joinedload(TradeDetails.token)).all()

    # If no trades are found, raise a 404 error
    if not trades:
        raise HTTPException(status_code=404, detail="No trades found")

    # Return the list of trades directly, FastAPI will use the response_model to serialize
    return trades

@router.get('/{index}', response_model=List[ExpirySchema])
async def get_index_expiry(index:str, db: Session = Depends(get_db)):
    response = retrieve_expiry(index, db)
    if not response:  return JSONResponse({"success": False, "data":response}, status_code=404)
    return JSONResponse({"success": True, "data":response}, status_code=200)


@router.get('/{index}/{expiry}', response_model=List[ExpirySchema])
async def get_index_strike_price(index:str, expiry: str,  db: Session = Depends(get_db)):
    response = retrieve_strike_price(index, expiry, db)
    if not response:  return JSONResponse({"success": False, "data":response}, status_code=404)
    return JSONResponse({"success": True, "data":response}, status_code=200)

@router.get("/strategies/", response_model=List[StrategyDetailsSchema])
def get_all_strategies(db: Session = Depends(get_db)):
    strategies = db.query(StrategyValue).all()
    print(strategies)
    if not strategies:
        raise HTTPException(status_code=404, detail="No strategies found")
    return strategies
# @router.get('/order/{order}', response_model=List[Order])
# async def get_fetch_previous_order(order_id:int, db: Session = Depends(get_db)):
#     response = fetch_previous_orders(order_id, db)
#     if not response:  return JSONResponse({"success": False, "data":response}, status_code=404)
#     return JSONResponse({"success": True, "data":response}, status_code=200)

@router.get('/order/', response_model=List[Order])
async def get_fetch_previous_orders(db: Session = Depends(get_db)):
    response = fetch_previous_orders(db)
    if not response:  return JSONResponse({"success": False, "data":response}, status_code=404)
    return JSONResponse({"success": True, "data":response}, status_code=200)

# from .strategy import BaseStrategy, max_transactions_indicator, instrument_reader, smart_api_provider
@router.get('/trades/')
def get_trade_details(db: Session = Depends(get_db)):
    return JSONResponse({"success":True})


@router.post("/tradingdata/", response_model=TradingDataResponse)
def create_trading_data(trading_data: TradingDataCreate, db: Session = Depends(get_db)):
    db_trading_data = TradingData(**trading_data.dict())
    db.add(db_trading_data)
    db.commit()
    db.refresh(db_trading_data)
    return db_trading_data

# PUT Endpoint to update trading data
@router.put("/tradingdata/{data_id}", response_model=TradingDataResponse)
def update_trading_data(data_id: int, trading_data: TradingDataUpdate, db: Session = Depends(get_db)):
    db_trading_data = db.query(TradingData).filter(TradingData.id == data_id).first()
    if not db_trading_data:
        raise HTTPException(status_code=404, detail="Trading Data not found")

    for key, value in trading_data.dict(exclude_unset=True).items():
        setattr(db_trading_data, key, value)

    db.commit()
    db.refresh(db_trading_data)
    return db_trading_data