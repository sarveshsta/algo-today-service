from typing import List

import fastapi
from fastapi import Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from config.database.config import get_db
from trades.managers import *
from trades.schema import ExpirySchema, TokenSchema, Order

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
