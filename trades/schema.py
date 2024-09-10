from pydantic import BaseModel


class TokenSchema(BaseModel):
    token: str
    symbol: str
    name: str
    expiry: str
    strike: str
    lotsize: str
    instrumenttype: str
    exch_seg: str
    tick_size: str

    class Config:
        from_attributes = True




class TradeDetailsSchema(BaseModel):
    user_id : str
    token : str
    signal : str
    price : float

    class Config:
        from_attributes = True

class ExpirySchema(BaseModel):
    token: str
    symbol: str
    index: str
    expiry: str
    class Config:
        from_attributes = True

class IndexData(BaseModel):
    index: str
    strike_price: int
    expiry: str
    option: str
    chart_time: str
    quantity: int | None
    
    class Config:
        from_attributes = True

class StartStrategySchema(BaseModel):
    user_id: str
    strategy_id: str
    index_list: list[IndexData]
    
    class Config:
        from_attributes = True
        
class Order(BaseModel):
    unique_order_id: str
    symboltoken: str
    signal: str
    price: float
    status: str
    quantity: str
    ordertype: str
    producttype: str
    duration: str
    stoploss: float
    average_price: float
    exchange_order_id: str
    transactiontime: int

    class Config:
        from_attributes = True
