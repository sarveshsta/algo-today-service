from typing import List

import fastapi
from fastapi import Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from config.database.config import get_db
from trades.managers import delete_all_tokens, fetch_tokens, get_tokens, retrieve_token
from trades.schema import TokenSchema

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


@router.get("/{symbol}", response_model=TokenSchema)
def retrieve_token_by_symbol(symbol: str, db: Session = Depends(get_db)):
    return retrieve_token(symbol, db)
