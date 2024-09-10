from sqlalchemy.orm import Session
from contextlib import contextmanager
from config.database.config import get_db
from fastapi import Depends
from .models import TradeDetails
from .schema import TradeDetailsSchema

db = Depends(get_db)


def save_tradedetails(trade_data: TradeDetailsSchema):
    # Create TradeDetails instance dynamically using the schema data
    trade_details = TradeDetails(
        user_id=trade_data.user_id, token=trade_data.token, signal=trade_data.signal, price=trade_data.price
    )

    # Add the new record to the session and commit
    try:
        db.add(trade_details)
        db.commit()
        db.refresh(trade_details)  # Refresh to get any new data (e.g., auto-generated fields)
    except Exception as e:
        db.rollback()  # Rollback in case of any error
        raise # Optionally raise the exception after rollback
