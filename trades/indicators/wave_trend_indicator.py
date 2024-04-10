import indicator_settings as ids
import statistics as stats
from collections import deque
from itertools import islice
from decimal import Decimal

class WaveTrendOscillatorIndicator():


    def __init__(self, timeframe, timestamp, channel_length, average_length, histogram_smoothing, histogram_multiplier, pivot_right_len, pivot_left_len, max_lookback, min_lookback, config):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.channel_length = channel_length
        self.average_length = average_length
        self.histogram_smoothing = histogram_smoothing
        self.histogram_multiplier = Decimal(histogram_multiplier)
        self.pivot_right_len = pivot_right_len
        self.pivot_left_len = pivot_left_len
        self.max_lookback = max_lookback
        self.min_lookback = min_lookback

        self.close_queue_len= max(self.channel_length, self.average_length)

        self.ohcl_queue = deque(maxlen=self.close_queue_len)

        self.close_queue = deque(maxlen=self.close_queue_len)
        lens = [self.pivot_left_len, self.pivot_right_len, self.max_lookback, self.min_lookback]

        self.high_low_queue_len = max(lens)
        print(lens)
        self.high_queue = deque(maxlen=self.high_low_queue_len)
        self.low_queue = deque(maxlen=self.high_low_queue_len)

        self.d1_queue = deque(maxlen=self.channel_length)
        self.ci_queue = deque(maxlen=self.average_length)
        self.wt1_queue = deque(maxlen=3)
        self.wt2_queue = deque(maxlen=3)
        self.dif_queue = deque(maxlen=self.histogram_smoothing)
        self.hist_queue = deque(maxlen=2)

        self.esa = None
        self.d1 = None


        self.wt1 = None
        self.wt2 = None
        self.hist = None
        self.hist_color = ""

        self.config = config

        self.current_value = None

        self.long_condition = False
        self.short_condition = False

        lens = [self.channel_length, self.average_length, self.histogram_smoothing, self.max_lookback, self.min_lookback, self.pivot_left_len, self.pivot_right_len]
        self.max_len = max(lens) * 2
        self.warmed_up = False


    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.close_queue.appendleft(close)
        self.high_queue.appendleft(high)
        self.low_queue.appendleft(low)

        ohcl = (open + high + low + close) / 4
        self.ohcl_queue.appendleft(ohcl)


        if len(self.close_queue) == self.close_queue_len and len(self.high_queue) == self.high_low_queue_len and len(self.low_queue) == self.high_low_queue_len and len(self.ohcl_queue) == self.close_queue_len:
            self.esa = self.calculate_ema(deque(islice(self.ohcl_queue, 0, self.channel_length-1)), self.esa)
            self.d1_queue.appendleft(abs(ohcl - self.esa))
            if len(self.d1_queue) == self.channel_length:
                self.d1 = self.calculate_ema(self.d1_queue, self.d1)
                ci = (ohcl - self.esa) / (Decimal(0.015) * self.d1)
                self.ci_queue.appendleft(ci)
                if len(self.ci_queue) == self.average_length:
                    self.wt1 = self.calculate_ema(self.ci_queue, self.wt1)
                    self.wt1_queue.appendleft(self.wt1)
                    if len(self.wt1_queue) == 3:
                        self.wt2 = sum(self.wt1_queue) / len(self.wt1_queue)
                        self.wt2_queue.appendleft(self.wt2)
                        dif = (self.wt1 - self.wt2) * Decimal(1.5)
                        self.dif_queue.appendleft(dif)
                        if len(self.dif_queue) == self.histogram_smoothing:
                            self.hist = self.calculate_ema(self.dif_queue, self.hist)
                            self.hist_queue.appendleft(self.hist* self.histogram_multiplier)
                            self.current_value = self.hist
                            if len(self.hist_queue) == 2:
                                hist_0 = self.hist_queue[0]
                                hist_1 = self.hist_queue[1]
                                if hist_0 > hist_1 and hist_0 < 0:
                                    self.hist_color = "PINK"
                                elif hist_0 > hist_1 and hist_0 > 0:
                                    self.hist_color = "DARK GREEN"
                                elif hist_0 < hist_1 and hist_0 > 0:
                                    self.hist_color = "GREEN"
                                elif hist_0 < hist_1 and hist_0 < 0:
                                    self.hist_color = "RED"
                                else:
                                    self.hist_color = ""

                                self.check_conditions()

    def check_conditions(self):
        long_conditions = []
        short_conditions = []



        if self.config["long"]["channel_above"] is None or self.wt1 > self.config["long"]["channel_above"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)

        if self.config["long"]["channel_below"] is None or self.wt1 < self.config["long"]["channel_below"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["channel_cross"] is None or (self.config["long"]["channel_cross"] == "POSITIVE" and self.wt1_queue[0] > self.wt2_queue[0] and self.wt1_queue[1] < self.wt2_queue[1]) or (self.config["long"]["channel_cross"] == "NEGATIVE" and self.wt1_queue[0] < self.wt2_queue[0] and self.wt1_queue[1] > self.wt2_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["channel_direction"] is None or (self.config["long"]["channel_direction"] == "RISING" and self.wt1_queue[0] > self.wt1_queue[1]) or (self.config["long"]["channel_direction"] == "FALLING" and self.wt1_queue[0] < self.wt1_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if len(self.config["long"]["histogram_color"]) == 0 or self.hist_color in self.config["long"]["histogram_color"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["histogram_direction"] is None or (self.config["long"]["histogram_direction"] == "ASCENDING" and self.hist_queue[0] > self.hist_queue[1]) or (self.config["long"]["histogram_direction"] == "DESCENDING" and self.hist_queue[0] < self.hist_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["histogram_above"] is None or self.hist_queue[0] > self.config["long"]["histogram_above"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["histogram_below"] is None or self.hist_queue[0] < self.config["long"]["histogram_below"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)



        if self.config["short"]["channel_above"] is None or self.wt1 > self.config["short"]["channel_above"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["channel_below"] is None or self.wt1 < self.config["short"]["channel_below"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["channel_cross"] is None or (self.config["short"]["channel_cross"] == "POSITIVE" and self.wt1_queue[0] > self.wt2_queue[0] and self.wt1_queue[1] < self.wt2_queue[1]) or (self.config["short"]["channel_cross"] == "NEGATIVE" and self.wt1_queue[0] < self.wt2_queue[0] and self.wt1_queue[1] > self.wt2_queue[1]):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["channel_direction"] is None or (self.config["short"]["channel_direction"] == "RISING" and self.wt1_queue[0] > self.wt1_queue[1]) or (self.config["short"]["channel_direction"] == "FALLING" and self.wt1_queue[0] < self.wt1_queue[1]):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if len(self.config["short"]["histogram_color"]) == 0 or self.hist_color in self.config["short"]["histogram_color"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["histogram_direction"] is None or (self.config["short"]["histogram_direction"] == "ASCENDING" and self.hist_queue[0] > self.hist_queue[1]) or (self.config["short"]["histogram_direction"] == "DESCENDING" and self.hist_queue[0] < self.hist_queue[1]):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["histogram_above"] is None or self.hist_queue[0] > self.config["short"]["histogram_above"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["histogram_below"] is None or self.hist_queue[0] < self.config["short"]["histogram_below"]:
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


    def calculate_ema(self, list_item, current_value):
        if current_value is None:
            current_value = sum(list_item) / len(list_item)
            return current_value
        else:
            k = Decimal(2 / (len(list_item) + 1))
            current_value = list_item[0] * k + current_value * (1 - k)
            return current_value
