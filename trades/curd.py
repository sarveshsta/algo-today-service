from sqlalchemy.orm import Session
from models import TradeDetails

def save_trade(new_trade: TradeDetails, db:Session) -> TradeDetails:

    db.add(new_trade)
    db.commit()
    db.refresh(new_trade)
    return new_trade