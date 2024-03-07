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

class ExpirySchema(BaseModel):
    token: str
    symbol: str
    index: str
    expiry: str
    class Config:
        from_attributes = True
