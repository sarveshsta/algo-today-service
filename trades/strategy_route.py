from typing import Dict
import asyncio
import json
import fastapi
import logging
import requests
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from trades.schema import StartStrategySchema
from trades.strategy.constant import NFO_DATA_URL
from .managers import strategy_start, strategy_stop

router = fastapi.APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tasks: Dict[str, asyncio.Task] = {}

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
        return JSONResponse(response)
    except Exception as exc:
        logger.info(f"Error in running strategy", exc)
        response = {
            "message": f"strategy failed to start, {exc}, ",
            "success": False,
        }
        return JSONResponse(response)

# Stop strategy endpoint
@router.get("/stop_strategy/{strategy_id}")
async def stop_strategy(strategy_id):
    await strategy_stop(strategy_id)
    return JSONResponse({"message": "Strategy stopped", "success": True})


#get all trades with strik prices
@router.get("/get-margin-calculator")
def get_all_strike_prices():
    logger.info("value")
    response = requests.get(NFO_DATA_URL)
    response.raise_for_status()
    data = response.json()
    with open("data.json", "w") as json_file:
        json.dump(data, json_file, indent=4)
    return JSONResponse({"message": "all strike list", "success": True})
