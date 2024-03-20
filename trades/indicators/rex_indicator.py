import indicator_settings as ids
import statistics as stats
from collections import deque
from itertools import islice
import math
from decimal import Decimal

class RexOscillatorIndicator():


    def __init__(self, timeframe, timestamp, ma_type, smoothing_length, signal_ma_type, signal_smoothing_length, config=None, is_exit=False):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.ma_type = ma_type
        self.smoothing_length = smoothing_length
        self.signal_ma_type = signal_ma_type
        self.signal_smoothing_length = signal_smoothing_length

        self.tvb_queue = deque(maxlen=self.smoothing_length)
        self.tvb_sig_queue = deque(maxlen=self.signal_smoothing_length)

        self.current_value = None
        self.current_sig = None

        self.rex_queue = deque(maxlen=2)
        self.signal_queue = deque(maxlen=2)

        self.is_exit = is_exit
        self.config = config


        lens = [self.smoothing_length, self.signal_smoothing_length]
        self.max_len = max(lens) * 2
        self.warmed_up = False

        self.long_exit = False
        self.short_exit = False
        self.last_finished_tvb = None
        self.last_finished_rex = None
        self.last_finished_signal = None

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

    def calculate_value(self, open, high, low, close, volume, timestamp, is_exit=False, is_finished_bar=False):
        tvb = 3 * close - open - high - low
        # self.tvb_queue.appendleft(tvb)
        # self.tvb_sig_queue.appendleft(tvb)
        self.update_queues(
            is_finished_bar,
            ('last_finished_tvb', 'tvb_queue', tvb),
            ('last_finished_tvb', 'tvb_sig_queue', tvb),
        )



        if len(self.tvb_queue) == self.smoothing_length and len(self.tvb_sig_queue) == self.signal_smoothing_length:
            if self.ma_type == "SMA":
                self.current_value = self.calculate_sma(self.tvb_queue)
            elif self.ma_type == "EMA":
                self.current_value = self.calculate_ema(self.tvb_queue, self.current_value)
            elif self.ma_type == "TENKAN":
                self.current_value = self.calculate_tenkan(self.tvb_queue)

            if self.signal_ma_type == "SMA":
                self.current_sig = self.calculate_sma(self.tvb_sig_queue)
            elif self.signal_ma_type == "EMA":
                self.current_sig = self.calculate_ema(self.tvb_sig_queue, self.current_sig)
            elif self.signal_ma_type == "TENKAN":
                self.current_sig = self.calculate_tenkan(self.tvb_sig_queue)

            self.rex_queue.appendleft(self.current_value)
            self.signal_queue.appendleft(self.current_sig)
            self.update_queues(
                is_finished_bar,
                ('last_finished_rex', 'rex_queue', self.current_value),
                ('last_finished_signal', 'signal_queue', self.current_sig),
            )

            if self.config is not None and len(self.rex_queue) == 2 and len(self.signal_queue) == 2:
                self.check_conditions()



    def check_conditions(self):
        long_conditions = []
        short_conditions = []

        if not self.config["long"]["cross_above_signal_line"] or (self.config["long"]["cross_above_signal_line"] and self.rex_queue[0] > self.signal_queue[0] and self.rex_queue[1] < self.signal_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)

        if not self.config["long"]["cross_below_signal_line"] or (self.config["long"]["cross_below_signal_line"] and self.rex_queue[0] < self.signal_queue[0] and self.rex_queue[1] > self.signal_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)

        if self.config["long"]["oversold_level"] is  None or self.rex_queue[0] <= self.config["long"]["oversold_level"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["over_bought_level"] is None or self.rex_queue[0] >= self.config["long"]["over_bought_level"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)



        if not self.config["short"]["cross_above_signal_line"] or (self.config["short"]["cross_above_signal_line"] and self.rex_queue[0] > self.signal_queue[0] and self.rex_queue[1] < self.signal_queue[1]):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if not self.config["short"]["cross_below_signal_line"] or (self.config["short"]["cross_below_signal_line"] and self.rex_queue[0] < self.signal_queue[0] and self.rex_queue[1] > self.signal_queue[1]):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["oversold_level"] is None or self.rex_queue[0] <= self.config["short"]["oversold_level"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["over_bought_level"] is None or self.rex_queue[0] >= self.config["short"]["over_bought_level"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)

        if True in long_conditions and not False in long_conditions:
            self.long_exit = True
        else:
            self.long_exit = False

        if True in short_conditions and not False in short_conditions:
            self.short_exit = True
        else:
            self.short_exit = False




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
        y = 15
        norm = 0.0
        sum = 0.0
        for i in range(y):
            weight = (y - i) * y
            norm += weight
            sum += list_item[i] * weight
        return sum / norm

    def calculate_ema(self, list_item, current_value):
        if current_value is None:
            current_value = sum(list_item) / len(list_item)
            return current_value
        else:
            k = Decimal(2 / (len(list_item) + 1))
            current_value = list_item[0] * k + current_value * (1 - k)
            return current_value


    def calculate_tenkan(self, list_item):
        current_value = 0.5 * (max(list_item) + min(list_item))
        return current_value

