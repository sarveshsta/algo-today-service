import indicator_settings as ids
import statistics as stats
from collections import deque
from itertools import islice
import math
from .moving_averages import ExponentialMovingAverage
from decimal import Decimal


class AverageTrueRangeIndicator():


    def __init__(self, timeframe, timestamp, length, portfolio):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.length = length
        self.portfolio = portfolio
        self.close_queue = deque(maxlen=2)
        self.tr_queue = deque(maxlen=self.length)
        self.ema = ExponentialMovingAverage(self.timeframe, self.timestamp, self.length)
        self.current_value = None
        self.warmed_up = False
        self.atr_queue = deque(maxlen=2)
        self.atr_at_entry = None
        self.close_at_entry = None
        lens = [self.length]
        self.max_len = max(lens) * 2

    def calculate_rma(self, list_item, length, current_value):
        alpha = Decimal(1/length)

        if current_value is None:
            current_value = self.calculate_sma(list_item)
        else:
            current_value = alpha * list_item[0] + (1 - alpha) * current_value
        return current_value

    def calculate_sma(self, list_item):
        current_value = Decimal(sum(list_item) / len(list_item))
        return current_value


    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.close_queue.appendleft(close)
        #print(f"CLOSE {close}")
        if len(self.close_queue) == 2:
            tr_component_1 = high - low
            tr_component_2 = abs(high - self.close_queue[1])
            tr_component_3 = abs(low - self.close_queue[1])
            tr_list = [tr_component_1, tr_component_2, tr_component_3]
            tr = max(tr_list)
            self.tr_queue.appendleft(tr)
            if len(self.tr_queue) == self.length:
                #self.current_value = self.ema.calculate_ema(self.tr_queue, self.current_value)
                self.current_value = self.calculate_rma(self.tr_queue, len(self.tr_queue), self.current_value)
                self.atr_queue.appendleft(self.current_value)



    def get_atr_entry(self, record):
        if record and self.atr_at_entry is None:
            #print(f"INVESTED   {self.atr_queue[1]}")
            self.atr_at_entry = self.atr_queue[0]
            self.close_at_entry = self.close_queue[0]
        elif not self.portfolio.invested() and not self.portfolio.bot_has_open_order():
            self.atr_at_entry = None
            self.close_at_entry = None