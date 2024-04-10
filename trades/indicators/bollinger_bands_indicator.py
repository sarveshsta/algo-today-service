import indicator_settings as ids
from collections import deque
from decimal import Decimal



class BollingerBandsIndicator():


    def __init__(self, timeframe, timestamp, config, length, ma_type, source):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.config = config

    def calculate_value(self, open, high, low, close, volume, timestamp):
        if self.source == "CLOSE":
            src = close
        elif self.source == "OPEN":
            src = open
        elif self.source == "HIGH":
            src = high
        elif self.source == "LOW":
            src = low
        elif self.source == "HL2":
            src = (high + low) / 2
        elif self.source == "HLC3":
            src = (high + low + close) / 3
        elif self.source == "OHLC4":
            src = (open + high + low + close) / 4
        elif self.source == "HLCC4":
            src = (high + low + close + close) / 4
        else:
            raise Exception(f"Selected incorrect Source Value for Laguerre RSI, {self.source} is incorrect")
        self.basis = self.ma(src, self.length, self.ma_type)
        self.upper
        self.lower

    def ma(self, source, length, _type):
        if _type == "SMA":
            pass
        elif _type == "SMA":
            pass

    def check_conditions(self):
        long_conditions = []
        short_conditions = []