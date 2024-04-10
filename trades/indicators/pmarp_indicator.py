

import indicator_settings as ids
import statistics as stats
from collections import deque
from itertools import islice
import datetime
import math
from decimal import Decimal


class PMARPIndicator():


    def __init__(self, timeframe, timestamp, price_source, indicator, use_ma, ma_length, signal_ma_length, ma_type, lookback, config, is_exit=False):
        #print("WHY IS THIS BEING CREATED")
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.price_source = price_source
        self.indicator = indicator
        self.use_ma = use_ma
        self.ma_length = ma_length
        self.signal_ma_length = signal_ma_length
        self.ma_type = ma_type
        self.lookback = lookback
        self.is_exit = is_exit
        self.config = config

        self.source_queue = deque(maxlen=self.ma_length)
        self.volume_queue = deque(maxlen=max(self.ma_length, self.signal_ma_length))
        self.volume_x_price_queue = deque(maxlen=self.ma_length)

        self.pmar_high = 1
        self.pmar_low = 1

        self.ma = None
        self._pmar = None
        self.bar_index = 0
        self.pmar_queue = deque(maxlen=self.lookback)
        self.signal_ma = None

        self.ma_value = None

        self.plotline_queue = deque(maxlen=self.signal_ma_length)
        self.plotline_volume_queue = deque(maxlen=self.signal_ma_length)

        self.signal_ma_queue = deque(maxlen=2)
        self.current_value = None
        lens = [self.ma_length, (self.signal_ma_length*self.ma_length), self.lookback]
        self.max_len = max(lens) * 2
        self.warmed_up = False
        self.long_condition = False
        self.short_condition = False
        self.last_finished_source = None
        self.last_finished_volume = None
        self.last_finished_volume_x_price = None
        self.last_finished_plotline = None
        self.last_finished_plotline_x_volume = None
        self.last_finished_signal = None
        self.last_finished_pmar = None

        self.last_finished_pmar_high = None
        self.last_finished_pmar_low = None

    # This should go into utilities file
    def update_queues(self, is_finished_bar, *update_args):
        for variables in update_args:
            last_finished, deque_, value = variables
            deque_ = getattr(self, deque_)
            if not self.warmed_up or not self.is_exit:
                deque_.appendleft(value)
                setattr(self, last_finished, value)
            elif self.warmed_up and self.is_exit and not is_finished_bar:
                deque_.popleft()
                deque_.appendleft(value)
            elif self.warmed_up and self.is_exit and is_finished_bar:
                deque_.popleft()
                deque_.appendleft(getattr(self, last_finished))  # Append the last value
                deque_.appendleft(value)
                setattr(self, last_finished, value)

    def update_pmar_high_low(self, is_finished_bar, pmar):
        if not self.warmed_up or not self.is_exit:
            self.pmar_high = pmar if pmar > self.pmar_high else self.pmar_high
            self.pmar_low = pmar if pmar < self.pmar_low else self.pmar_low
            self.last_finished_pmar_high = self.pmar_high
            self.last_finished_pmar_low = self.pmar_low
        elif self.warmed_up and self.is_exit and not is_finished_bar:
            self.pmar_high = self.last_finished_pmar_high
            self.pmar_low = self.last_finished_pmar_low
            self.pmar_high = pmar if pmar > self.pmar_high else self.pmar_high
            self.pmar_low = pmar if pmar < self.pmar_low else self.pmar_low
        elif self.warmed_up and self.is_exit and is_finished_bar:
            self.pmar_high = self.last_finished_pmar_high
            self.pmar_low = self.last_finished_pmar_low
            self.pmar_high = pmar if pmar > self.pmar_high else self.pmar_high
            self.pmar_low = pmar if pmar < self.pmar_low else self.pmar_low
            self.last_finished_pmar_high = self.pmar_high
            self.last_finished_pmar_low = self.pmar_low



    def calculate_value(self, open, high, low, close, volume, timestamp, is_finished_bar=False):
        self.bar_index += 1
        if self.price_source == "CLOSE":
            src = close
        elif self.price_source == "OPEN":
            src = open
        elif self.price_source == "HIGH":
            src = high
        elif self.price_source == "LOW":
            src = low
        elif self.price_source == "HL2":
            src = (high + low) / 2
        elif self.price_source == "HLC3":
            src = (high + low + close) / 3
        elif self.price_source == "OHLC4":
            src = (open + high + low + close) / 4
        elif self.price_source == "HLCC4":
            src = (high + low + close + close) / 4
        else:
            raise Exception(f"Selected incorrect Source Value for PMARP, {self.price_source} is incorrect")
        self.update_queues(
            is_finished_bar,
            ('last_finished_source', 'source_queue', src),
            ('last_finished_volume', 'volume_queue', volume),
            ('last_finished_volume_x_price', 'volume_x_price_queue', volume * src),
        )

        if len(self.source_queue) == self.ma_length and len(self.volume_queue) == self.ma_length and len(self.volume_x_price_queue) == self.ma_length:

            self.ma = self.f_ma_val(self.source_queue, deque(islice(self.volume_queue, 0, self.ma_length-1)), self.volume_x_price_queue, self.ma_type, self.ma)
            pmar = src / self.ma
            self.pmarp = self.f_pmarp(src, self.source_queue, deque(islice(self.volume_queue, 0, self.ma_length-1)), self.volume_x_price_queue, self.ma_type, is_finished_bar)

            # self.pmar_high = pmar if pmar > self.pmar_high else self.pmar_high
            # self.pmar_low = pmar if pmar < self.pmar_low else self.pmar_low
            self.update_pmar_high_low(is_finished_bar, pmar)

            if pmar >= 1:
                PmarCRatio = 100 / (self.pmar_high - 1)
            else:
                PmarCRatio = 100 / (1 - self.pmar_low)

            if pmar >= 1:
                c_pmar = (((pmar - 1) * PmarCRatio) / 2) + 50
            else:
                c_pmar = ((pmar - self.pmar_low) * PmarCRatio) / 2

            plotline = self.pmarp if self.indicator == 'PRICE MOVING AVERAGE RATIO PERCENTILE' else pmar
            self.current_value = plotline
            # self.plotline_queue.appendleft(plotline)
            # self.plotline_volume_queue.appendleft(plotline * volume)
            self.update_queues(
                is_finished_bar,
                ('last_finished_plotline', 'plotline_queue', plotline),
                ('last_finished_plotline_x_volume', 'plotline_volume_queue', plotline * volume),
            )
            if len(self.plotline_queue) == self.signal_ma_length and len(self.plotline_volume_queue) == self.signal_ma_length:
                self.signal_ma = self.f_ma_val(self.plotline_queue, deque(islice(self.volume_queue, 0, self.signal_ma_length-1)), self.plotline_volume_queue, self.ma_type, self.signal_ma)
                # self.signal_ma_queue.appendleft(self.signal_ma)
                self.update_queues(
                    is_finished_bar,
                    ('last_finished_signal', 'signal_ma_queue', self.signal_ma),
                )
                if len(self.signal_ma_queue) == 2:
                    self.check_conditions()
                    #print(f"PMARMP {self.current_value} {datetime.datetime.now()} {close} {volume} {timestamp}")
                    # print(f"PMARMP {self.current_value}")
    def check_conditions(self):
        long_conditions = []
        short_conditions = []

        if self.config["long"]["below"] is None or self.plotline_queue[0] < self.config["long"]["below"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["above"] is None or self.plotline_queue[0] > self.config["long"]["above"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["cross_above"] is None or (self.config["long"]["cross_above"] != "SIGNAL_MA" and self.plotline_queue[0] > self.config["long"]["cross_above"] and self.plotline_queue[1] < self.config["long"]["cross_above"]) or (self.config["long"]["cross_above"] == "SIGNAL_MA" and self.plotline_queue[0] > self.signal_ma_queue[0] and self.plotline_queue[1] < self.signal_ma_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["cross_below"] is None or (self.config["long"]["cross_below"] != "SIGNAL_MA" and self.plotline_queue[0] < self.config["long"]["cross_below"] and self.plotline_queue[1] > self.config["long"]["cross_below"]) or (self.config["long"]["cross_below"] == "SIGNAL_MA" and self.plotline_queue[0] < self.signal_ma_queue[0] and self.plotline_queue[1] > self.signal_ma_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)



        if self.config["short"]["below"] is None or self.plotline_queue[0] < self.config["short"]["below"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)

        if self.config["short"]["above"] is None or self.plotline_queue[0] > self.config["short"]["above"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["cross_above"] is None or (self.config["short"]["cross_above"] != "SIGNAL_MA" and self.plotline_queue[0] > self.config["short"]["cross_above"] and self.plotline_queue[1] < self.config["short"]["cross_above"]) or (self.config["short"]["cross_above"] == "SIGNAL_MA" and self.plotline_queue[0] > self.signal_ma_queue[0] and self.plotline_queue[1] < self.signal_ma_queue[1]):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["cross_below"] is None or (self.config["short"]["cross_below"] != "SIGNAL_MA" and self.plotline_queue[0] < self.config["short"]["cross_below"] and self.plotline_queue[1] > self.config["short"]["cross_below"]) or (self.config["short"]["cross_below"] == "SIGNAL_MA" and self.plotline_queue[0] < self.signal_ma_queue[0] and self.plotline_queue[1] > self.signal_ma_queue[1]):
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


    def f_ma_val(self, source_queue, volume_queue, volume_price_queue, ma_type, current_value, is_fpmarp=False):
        if ma_type == "SMA":
            current_value = self.calculate_sma(source_queue)
        elif ma_type == "EMA":
            current_value = self.calculate_ema(source_queue, current_value)
        elif ma_type == "VWMA":
            current_value = self.calculate_vwma(volume_price_queue, volume_queue)
        else:
            raise Exception(f"Invalid MA Type selected in PMARP Indicator, {ma_type} is invalid")
        if is_fpmarp:
            self.ma_value = current_value
        return current_value


    def f_pmarp(self, source, source_queue, volume_queue, volume_price_queue, ma_type, is_finished_bar):
        self._pmar = abs(source / self.f_ma_val(source_queue, volume_queue, volume_price_queue, ma_type, self.ma_value, True))
        # self.pmar_queue.appendleft(self._pmar)
        self.update_queues(
            is_finished_bar,
            ('last_finished_pmar', 'pmar_queue', self._pmar),
        )

        _pmarpSum = 0

        if self.bar_index < self.lookback:
            _len = self.bar_index
        else:
            _len = self.lookback

        if len(self.pmar_queue) >= _len:

            for i in range(1, _len+1):
                if i >= len(self.pmar_queue):
                    break
                if self.pmar_queue[i] <= self._pmar:
                    _pmarpSum += 1

        current_value = _pmarpSum / _len * 100 if self.bar_index >= self.ma_length else None
        return Decimal(current_value)

    def calculate_sma(self, list_item):
        current_value = sum(list_item) / len(list_item)
        return current_value


    def calculate_wma(self, list_item):
        y = 15
        norm = 0.0
        sum = 0.0
        for i in range(y):
            weight = (y - i) * y
            norm += weight
            sum += list_item[i] * weight
        return sum / norm



    def calculate_vwma(self, list_item_1, list_item_2):
        current_value = self.calculate_sma(list_item_1) / self.calculate_sma(list_item_2)

        return current_value


    def calculate_ema(self, list_item, current_value):
        if current_value is None:
            current_value = sum(list_item) / len(list_item)
            return current_value
        else:
            k = 2 / (len(list_item) + 1)
            current_value = list_item[0] * k + current_value * (1 - k)
            return current_value