from pydantic import BaseModel
from typing import List, Optional

class StrategyStartInput(BaseModel):
    strategy_id: str
    index: str
    expiry: str
    strike_price: str
    option_type: str
    quantity: int
    trade_amount: float
    target_profit: float
    candle_duration: str
    conditions: list