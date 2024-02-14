from datetime import datetime


class Token:
    def __init__(
        self,
        token_id: int,
        symbol: str,
        name: str,
        expiry: datetime.timestamp,
        strike: float,
        lot_size: int,
        instrument_type: str,
        exch_seg: str,
        tick_size: float,
    ) -> None:
        self.__token_id = token_id
        self.symbol = symbol
        self.name = name
        self.expiry = expiry
        self.strike = strike
        self.lot_size = lot_size
        self.instrument_type = instrument_type
        self.exch_seg = exch_seg
        self.tick_size = tick_size

    @property
    def token_id(self) -> int:
        return self.__token_id
