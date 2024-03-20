import indicator_settings as ids
import statistics as stats
from collections import deque
from itertools import islice
from .atr_indicator import AverageTrueRangeIndicator
import math

class ATRBandsIndicator():



    def __init__(self, timeframe, timestamp, atr_period, atr_multiplier, tp_scale_factor):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.tp_scale_factor = tp_scale_factor

        self.atr = AverageTrueRangeIndicator(self.timeframe, self.timestamp, self.atr_period)

        self.source_queue = deque(maxlen=self.atr_period)

        self.current_value = None

        self.warmed_up = False

        lens = [self.atr_period]
        self.max_len = max(lens) * 2







    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.atr.calculate_value(open, high, low, close, volume, timestamp)

        if self.atr.current_value is not None:
            scaledATR = self.atr.current_value * self.atr_multiplier
            upperATRBand = close + scaledATR
            lowerATRBand = close - scaledATR

            scaledTPLong = close + ((close - lowerATRBand) * self.tp_scale_factor)
            scaledTPShort = close - ((upperATRBand - close) * self.tp_scale_factor)
