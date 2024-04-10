import indicator_settings as ids
import statistics as stats
from collections import deque
from itertools import islice
import math
from decimal import Decimal

class McGinleyDynamicIndicator():


    def __init__(self, source, period, constant, average_mode, timeframe, timestamp):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.source = source
        self.period = period
        self.constant = constant
        self.average_mode = average_mode

        self.source_queue = deque(maxlen=self.period + 1)
        self.current_ma = None
        self.mg = None
        self.mg_color = ""

        self.current_value = None

        lens = [self.period]
        self.max_len = max(lens) * 2
        self.warmed_up = False
        self.value_queue = deque(maxlen=2)
        self.slope = None

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

        self.source_queue.appendleft(src)

        if len(self.source_queue) == self.period + 1:
            src_manip = self.calculate_sma(deque(islice(self.source_queue, 0, (len(self.source_queue)-2))))
            if self.average_mode == "EMA":
                self.current_ma = self.calculate_ema(deque(islice(self.source_queue, 1, None)), self.current_ma)
            elif self.average_mode == "SMA":
                self.current_ma = self.calculate_sma(deque(islice(self.source_queue, 1, None)))
            elif self.average_mode == "SMMA":
                self.current_ma = self.calculate_smma(deque(islice(self.source_queue, 1, None)), self.current_ma)
            elif self.average_mode == "LWMA":
                self.current_ma = self.calculate_wma(deque(islice(self.source_queue, 1, None)))
            else:
                raise Exception(f"Selected incorrect Moving Average Mode in MCGinley, Mode {self.average_mode} is wrong")
            self.mg = self.current_ma + (src_manip - self.current_ma) / Decimal(self.constant * self.period * math.pow(src_manip / self.current_ma, 4))
            if close > self.mg:
                self.mg_color = "GREEN"
            else:
                self.mg_color = "RED"

            self.current_value = self.mg
            self.value_queue.appendleft(self.current_value)
            if len(self.value_queue) == 2:
                x1, y1 = 0, self.value_queue[1]
                x2, y2 = 1, self.value_queue[0]
                self.slope = (y2 - y1) / (x2 - x1)

    def calculate_sma(self, list_item):
        current_value = sum(list_item) / len(list_item)
        return current_value

    def calculate_smma(self, list_item, current_value):
        length = len(list_item)
        outer = sum(list_item) / length
        if current_value is None:
            return outer
        else:
            current_value = (current_value * (length - 1) + list_item[-1]) / length
            return current_value


    def calculate_wma(self, list_item):
        y = self.period
        norm = Decimal(0.0)
        sum = Decimal(0.0)
        for i in range(y):
            weight = (y - i) * y
            norm += weight
            sum += list_item[i] * Decimal(weight)
        return sum / norm


    def calculate_ema(self, list_item, current_value):
        if current_value is None:
            current_value = sum(list_item) / len(list_item)
            return current_value
        else:
            k = Decimal(2 / (len(list_item) + 1))
            current_value = list_item[0] * k + current_value * (1 - k)
            return current_value