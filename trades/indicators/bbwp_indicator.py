import indicator_settings as ids
import statistics as stats
from collections import deque
from itertools import islice
from .stdev_indicator import StandardDeviationIndicator
from decimal import Decimal
import math

class BBWPIndicator():


    def __init__(self, timeframe, timestamp, source, basis_type, length, lookback, use_ma_1, ma_1_type, ma_1_length, use_ma_2, ma_2_type, ma_2_length, config):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.source = source
        self.basis_type = basis_type
        self.length = length
        self.lookback = lookback
        self.use_ma_1 = use_ma_1
        self.ma_1_type = ma_1_type
        self.ma_1_length = ma_1_length
        self.use_ma_2 = use_ma_2
        self.ma_2_type = ma_2_type
        self.ma_2_length = ma_2_length

        self.stdev = StandardDeviationIndicator(self.timeframe, self.timestamp, self.length)


        self.bar_index = 0

        self._basis = None

        self.source_queue = deque(maxlen=self.length)
        self.volume_queue = deque(maxlen=self.length)
        self.volume_1_queue = deque(maxlen=self.ma_1_length)
        self.volume_2_queue = deque(maxlen=self.ma_2_length)
        self.volume_x_price_queue = deque(maxlen=self.length)

        self._bbw_queue = deque(maxlen=self.lookback)
        self.bbwp = None
        self.bbwpMA1 = None
        self.bbwpMA2 = None
        self.bbwpMA1_queue = deque(maxlen=2)
        self.bbwpMA2_queue = deque(maxlen=2)
        self.bbwp_queue_1 = deque(maxlen=self.ma_1_length)
        self.bbwp_queue_2 = deque(maxlen=self.ma_2_length)

        self.bbwp_volume_queue_1 = deque(maxlen=self.ma_1_length)
        self.bbwp_volume_queue_2 = deque(maxlen=self.ma_2_length)

        self.config = config

        self.current_value = None


        self.long_condition = False
        self.short_condition = False


        lens = [self.length, self.lookback, self.ma_1_length, self.ma_2_length]
        self.max_len = max(lens) * 2
        self.warmed_up = False

    def f_maType(self, source_queue, volume_queue, volume_price_queue, ma_type, current_value):
        if ma_type == "SMA":
            current_value = self.calculate_sma(source_queue)
        elif ma_type == "EMA":
            current_value = self.calculate_ema(source_queue, current_value)
        elif ma_type == "VWMA":
            current_value = self.calculate_vwma(volume_price_queue, volume_queue)
        else:
            raise Exception(f"Invalid MA Type selected in BBWP Indicator, {ma_type} is invalid")

        return current_value

    def calculate_ema(self, list_item, current_value):
        if current_value is None:
            current_value = sum(list_item) / len(list_item)
            return current_value
        else:
            k = Decimal(2 / (len(list_item) + 1))
            current_value = list_item[0] * k + current_value * (1 - k)
            return current_value


    def calculate_sma(self, list_item):
        current_value = Decimal(sum(list_item) / len(list_item))
        return current_value

    def f_bbwp(self, source_queue, volume_queue, volume_price_queue, ma_type, current_value):
        self._basis = self.f_maType(source_queue, volume_queue, volume_price_queue, ma_type, self._basis)
        current_value = None
        if len(source_queue) >= 2:
            #_dev = stats.stdev(source_queue)
            _dev = self.stdev.pine_stdev(source_queue, len(source_queue))
            _bbw = (self._basis + _dev - (self._basis - _dev)) / self._basis
            self._bbw_queue.appendleft(_bbw)

            if self.bar_index < self.lookback:
                _len = self.bar_index
            else:
                _len = self.lookback

            _bbwSum = 0

            if len(self._bbw_queue) >= _len:

                for i in range(1, _len+1):
                    if i >= len(self._bbw_queue):
                        break
                    if self._bbw_queue[i] <= _bbw:
                        _bbwSum += 1

            current_value = _bbwSum / _len * 100 if self.bar_index >= self.length else None
        if current_value is not None:
            current_value = Decimal(current_value)
        return current_value

    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.bar_index += 1
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
            raise Exception(f"Selected incorrect Source Value for BBWP, {self.source} is incorrect")

        self.source_queue.appendleft(src)
        self.volume_queue.appendleft(volume)
        self.volume_1_queue.appendleft(volume)
        self.volume_2_queue.appendleft(volume)
        self.volume_x_price_queue.appendleft(volume * src)

        self.bbwp = self.f_bbwp(self.source_queue, self.volume_queue, self.volume_x_price_queue, self.basis_type, self.bbwp)

        if self.bbwp is not None:
            self.current_value = self.bbwp
            self.bbwp_queue_1.appendleft(self.bbwp)
            self.bbwp_queue_2.appendleft(self.bbwp)

            self.bbwp_volume_queue_1.appendleft(self.bbwp * volume)
            self.bbwp_volume_queue_2.appendleft(self.bbwp * volume)

            if len(self.bbwp_queue_1) == self.ma_1_length and len(self.bbwp_volume_queue_1) == self.ma_1_length and len(self.volume_1_queue) == self.ma_1_length:
                self.bbwpMA1 = self.f_maType(self.bbwp_queue_1, self.volume_queue, self.bbwp_volume_queue_1, self.ma_1_type, self.bbwpMA1) if self.use_ma_1 else None
                if self.bbwpMA1 is not None:
                    self.bbwpMA1_queue.appendleft(self.bbwpMA1)
                if len(self.bbwpMA1_queue) == 2:
                    self.check_conditions()

            if len(self.bbwp_queue_2) == self.ma_2_length and len(self.bbwp_volume_queue_2) == self.ma_2_length and len(self.volume_2_queue) == self.ma_2_length:
                self.bbwpMA2 = self.f_maType(self.bbwp_queue_2, self.volume_queue, self.bbwp_volume_queue_2, self.ma_2_type, self.bbwpMA2) if self.use_ma_2 else None

            # print(f"BBWP {self.current_value}")




    def check_conditions(self):
        long_conditions = []
        short_conditions = []

        if self.config["long"]["below"] is None or self.bbwp_queue_1[0] < self.config["long"]["below"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["above"] is None or self.bbwp_queue_1[0] > self.config["long"]["above"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["cross_above"] is None or (self.config["long"]["cross_above"] != "SIGNAL_MA" and self.bbwp_queue_1[0] > self.config["long"]["cross_above"] and self.bbwp_queue_1[1] < self.config["long"]["cross_above"]) or (self.config["long"]["cross_above"] == "SIGNAL_MA" and self.bbwp_queue_1[0] > self.bbwpMA1_queue[0] and self.bbwp_queue_1[1] < self.bbwpMA1_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["cross_below"] is None or (self.config["long"]["cross_below"] != "SIGNAL_MA" and self.bbwp_queue_1[0] < self.config["long"]["cross_below"] and self.bbwp_queue_1[1] > self.config["long"]["cross_below"]) or (self.config["long"]["cross_below"] == "SIGNAL_MA" and self.bbwp_queue_1[0] < self.bbwpMA1_queue[0] and self.bbwp_queue_1[1] > self.bbwpMA1_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)





        if self.config["short"]["below"] is None or self.bbwp_queue_1[0] < self.config["short"]["below"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)

        if self.config["short"]["above"] is None or self.bbwp_queue_1[0] > self.config["short"]["above"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["cross_above"] is None or (self.config["short"]["cross_above"] != "SIGNAL_MA" and self.bbwp_queue_1[0] > self.config["short"]["cross_above"] and self.bbwp_queue_1[1] < self.config["short"]["cross_above"]) or (self.config["short"]["cross_above"] == "SIGNAL_MA" and self.bbwp_queue_1[0] > self.bbwpMA1_queue[0] and self.bbwp_queue_1[1] < self.bbwpMA1_queue[1]):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["cross_below"] is None or (self.config["short"]["cross_below"] != "SIGNAL_MA" and self.bbwp_queue_1[0] < self.config["short"]["cross_below"] and self.bbwp_queue_1[1] > self.config["short"]["cross_below"]) or (self.config["short"]["cross_below"] == "SIGNAL_MA" and self.bbwp_queue_1[0] < self.bbwpMA1_queue[0] and self.bbwp_queue_1[1] > self.bbwpMA1_queue[1]):
            short_conditions.append(True)
        else:
            short_conditions.append(False)


        if True in long_conditions and not False in long_conditions:
            self.long_condition = True
        else:
            self.long_condition = False

        if True in short_conditions and not False in short_conditions:
            self.short_condition = True
        else:
            self.short_condition = False