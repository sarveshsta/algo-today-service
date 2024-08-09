from typing import List
import asyncio
import json
import fastapi
from fastapi import Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from config.database.config import get_db
from trades.managers import *
from trades.schema import ExpirySchema, StartStrategySchema, TokenSchema, Order
import logging

router = fastapi.APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


@router.get('/order/', response_model=List[Order])
async def get_fetch_previous_orders(db: Session = Depends(get_db)):
    response = fetch_previous_orders(db)
    if not response:  return JSONResponse({"success": False, "data":response}, status_code=404)
    return JSONResponse({"success": True, "data":response}, status_code=200)

# from .strategy import BaseStrategy, max_transactions_indicator, instrument_reader, smart_api_provider
@router.get('/trades/')
def get_trade_details(db: Session = Depends(get_db)):
    return JSONResponse({"success":True})


# Start strategy endpoint
@router.post("/start_strategy")
async def start_strategy(strategy_params: StartStrategySchema):
    try:
        strategy_id = strategy_params.strategy_id
        index_and_candle_durations = {}
        quantity_index = {}
        logger.info(f"strategy_params.index_list: {strategy_params.index_list}")
        for index in strategy_params.index_list:
            index_and_candle_durations[f"{index.index}{index.expiry}{index.strike_price}{index.option}"] = index.chart_time
            quantity_index[f"{index.index}{index.expiry}{index.strike_price}{index.option}"] = index.quantity

        if strategy_params.strategy_id in tasks:
            raise HTTPException(status_code=400, detail="Strategy already running")
        
        await strategy_start(strategy_id, index_and_candle_durations, quantity_index)

        response = {
            "message": "strategy starts",
            "success": True,
            "strategy_id": strategy_id
        }
        logger.info("Response", response)
        return response
    except Exception as exc:
        logger.info(f"Error in running strategy", exc)
        response = {
            "message": f"strategy failed to start, {exc}, ",
            "success": False,
        }
        return response

# Stop strategy endpoint
@router.get("/stop_strategy/{strategy_id}")
async def stop_strategy(strategy_id):
    await strategy_stop(strategy_id)
    return {"message": "Strategy stopped", "success": True}


#get all trades with strik prices
@router.get("/get-margin-calculator")
def get_all_strike_prices():
    response = requests.get(NFO_DATA_URL)
    response.raise_for_status()
    data = response.json()
    with open("data.json", "w") as json_file:
        json.dump(data, json_file, indent=4)
    return {"message": "all strike list", "success": True}
