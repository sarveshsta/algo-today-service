import indicator_settings as ids
import statistics as stats
from collections import deque
from .stdev_indicator import StandardDeviationIndicator
from itertools import islice
from decimal import Decimal

class WaddahAttarExplosionIndicator():


    def __init__(self, timeframe, timestamp, sensitivity, fast_length, slow_length, channel_length, multiplier, deadzone_multiplier, config):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.sensitivity = Decimal(sensitivity)
        self.fast_length = fast_length
        self.slow_length = slow_length
        self.channel_length = channel_length
        self.multiplier = Decimal(multiplier)
        self.deadzone_multiplier = Decimal(deadzone_multiplier)
        self.stdev = StandardDeviationIndicator(timeframe, timestamp, slow_length)
        self.fast_queue = deque(maxlen=self.fast_length)
        self.slow_queue = deque(maxlen=self.slow_length)
        self.channel_queue = deque(maxlen=self.channel_length)


        self.fast_ema = None
        self.slow_ema = None

        self.macd_queue = deque(maxlen=2)

        self.close_queue = deque(maxlen=2)
        self.tr_queue = deque(maxlen=100)
        self.atr = None
        self.deadzone = None


        self.t1 = None
        self.e1 = None

        self.e1_plus_queue = deque(maxlen=2)
        self.e1_minus_queue = deque(maxlen=2)

        self.deadzone_plus_queue = deque(maxlen=2)
        self.deadzone_minus_queue = deque(maxlen=2)

        self.trend_up = 0
        self.trend_down = 0

        self.candle_color = ""

        self.trend_up_queue = deque(maxlen=2)
        self.trend_down_queue = deque(maxlen=2)

        self.config = config

        self.long_condition = False
        self.short_condition = False

        self.current_value = None

        lens = [self.fast_length, self.slow_length, self.channel_length, 100]
        self.max_len = max(lens) * 2
        self.warmed_up = False


    def calculate_rma(self, list_item, length, current_value):
        alpha = Decimal(1/length)

        if current_value is None:
            current_value = self.calculate_sma(list_item)
        else:
            current_value = alpha * list_item[0] + (1 - alpha) * current_value
        return current_value

    def calculate_sma(self, list_item):
        current_value = sum(list_item) / len(list_item)
        return current_value


    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.fast_queue.appendleft(close)
        self.slow_queue.appendleft(close)
        self.close_queue.appendleft(close)
        self.channel_queue.appendleft(close)
        if len(self.close_queue) == 2:
            first_tr = high - low
            second_tr = abs(high - self.close_queue[1])
            third_tr = abs(low - self.close_queue[1])
            tr_list = [first_tr, second_tr, third_tr]
            tr = max(tr_list)
            self.tr_queue.appendleft(tr)
            if len(self.tr_queue) == 100:
                self.atr = self.calculate_rma(self.tr_queue, len(self.tr_queue), self.atr)
                self.deadzone = self.atr * self.deadzone_multiplier
                if len(self.fast_queue) == self.fast_length and len(self.slow_queue) == self.slow_length:
                    self.macd_queue.appendleft(self.calculate_macd(self.fast_queue, self.slow_queue))
                    if len(self.macd_queue) == 2:
                        self.t1 = (self.macd_queue[0] - self.macd_queue[1]) * self.sensitivity
                        if len(self.channel_queue) == self.channel_length:
                            self.e1 = (self.calculate_bb_upper(self.channel_queue, self.multiplier)) - (self.calculate_bb_lower(self.channel_queue, self.multiplier))
                            #print(f"EXPLOSION LINE {self.e1}")

                            self.deadzone_plus_queue.appendleft(self.deadzone)
                            self.deadzone_minus_queue.appendleft(-self.deadzone)

                            self.e1_plus_queue.appendleft(self.e1)
                            self.e1_minus_queue.appendleft(-self.e1)

                            if self.t1 >= 0:
                                self.trend_up = self.t1
                            else:
                                self.trend_up = 0
                            if self.t1 < 0 :
                                self.trend_down = self.t1
                            else:
                                self.trend_down = 0
                            #print(self.t1)
                            self.trend_up_queue.appendleft(self.trend_up)
                            self.trend_down_queue.appendleft(self.trend_down)

                            if len(self.trend_up_queue) == 2 and len(self.trend_down_queue) == 2:
                                if self.trend_up != 0:
                                    self.current_value = self.trend_up
                                    if self.trend_up_queue[0] > self.trend_up_queue[1]:
                                        self.candle_color = "DARK GREEN"
                                    else:
                                        self.candle_color = "GREEN"
                                if self.trend_down != 0:
                                    self.current_value = self.trend_down
                                    if self.trend_down_queue[0] < self.trend_down_queue[1]:
                                        self.candle_color = "DARK RED"
                                    else:
                                        self.candle_color = "RED"
                                # print("BANDSSSSSSSSSS")
                                # print(self.e1_plus_queue[0])
                                # print(self.e1_minus_queue[0])
                                self.check_conditions()


    def check_conditions(self):
        long_conditions = []
        short_conditions = []
        if len(self.config["long"]["Candle_color"]) == 0 or self.candle_color in self.config["long"]["Candle_color"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if len(self.config["long"]["Candle_cross"]) == 0 or self.config["long"]["Candle_cross_direction"] != "above" or (self.config["long"]["Candle_cross_direction"] == "above" and ("EXPLOSION LINE" in self.config["long"]["Candle_cross"] and self.trend_up_queue[0] > self.e1_plus_queue[0] and self.trend_up_queue[1] < self.e1_plus_queue[1]) or ("DEADZONE" in self.config["long"]["Candle_cross"] and self.trend_up_queue[0] > self.deadzone_plus_queue[0] and self.trend_up_queue[1] < self.deadzone_plus_queue[1])):
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if len(self.config["long"]["Candle_cross"]) == 0 or self.config["long"]["Candle_cross_direction"] != "below" or (self.config["long"]["Candle_cross_direction"] == "below" and ("EXPLOSION LINE" in self.config["long"]["Candle_cross"] and self.trend_up_queue[0] < self.e1_plus_queue[0] and self.trend_up_queue[1] > self.e1_plus_queue[1]) or ("DEADZONE" in self.config["long"]["Candle_cross"] and self.trend_up_queue[0] < self.deadzone_plus_queue[0] and self.trend_up_queue[1] > self.deadzone_plus_queue[1])):
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["BB"] is None or (self.config["long"]["BB"] == "EXPANDING" and self.e1_plus_queue[0] > self.e1_plus_queue[1]) or (self.config["long"]["BB"] == "CONTRACTING" and self.e1_plus_queue[0] < self.e1_plus_queue[1]) or (self.config["long"]["BB"] == "FLAT" and self.e1_plus_queue[0] == self.e1_plus_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)




        if len(self.config["short"]["Candle_color"]) == 0 or self.candle_color in self.config["short"]["Candle_color"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if len(self.config["short"]["Candle_cross"]) == 0 or self.config["short"]["Candle_cross_direction"] != "above" or (self.config["short"]["Candle_cross_direction"] == "above" and ("EXPLOSION LINE" in self.config["short"]["Candle_cross"] and self.trend_down_queue[0] > self.e1_minus_queue[0] and self.trend_down_queue[1] < self.e1_minus_queue[1]) or ("DEADZONE" in self.config["short"]["Candle_cross"] and self.trend_down_queue[0] > self.deadzone_minus_queue[0] and self.trend_down_queue[1] < self.deadzone_minus_queue[1])):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if len(self.config["short"]["Candle_cross"]) == 0 or self.config["short"]["Candle_cross_direction"] != "below" or (self.config["short"]["Candle_cross_direction"] == "below" and ("EXPLOSION LINE" in self.config["short"]["Candle_cross"] and self.trend_down_queue[0] < self.e1_minus_queue[0] and self.trend_down_queue[1] > self.e1_minus_queue[1]) or ("DEADZONE" in self.config["short"]["Candle_cross"] and self.trend_down_queue[0] < self.deadzone_minus_queue[0] and self.trend_down_queue[1] > self.deadzone_minus_queue[1])):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["BB"] is None or (self.config["short"]["BB"] == "EXPANDING" and self.e1_minus_queue[0] > self.e1_minus_queue[1]) or (self.config["short"]["BB"] == "CONTRACTING" and self.e1_minus_queue[0] < self.e1_minus_queue[1]) or (self.config["short"]["BB"] == "FLAT" and self.e1_minus_queue[0] == self.e1_minus_queue[1]):
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


    def calculate_bb_upper(self, list_item, multiplier):

        basis = sum(list_item) / len(list_item)
        dev = multiplier * self.stdev.pine_stdev(list_item, len(list_item))
        current_value = basis + dev
        return current_value


    def calculate_bb_lower(self, list_item, multiplier):
        basis = sum(list_item) / len(list_item)
        dev = multiplier * self.stdev.pine_stdev(list_item, len(list_item))
        current_value = basis - dev
        return current_value


    def calculate_macd(self, list_item_fast, list_item_slow):
        if self.fast_ema is None:
            self.fast_ema = self.calculate_sma(list_item_fast)
        else:
            self.fast_ema = self.calculate_ema(list_item_fast, self.fast_ema)
        if self.slow_ema is None:
            self.slow_ema = self.calculate_sma(list_item_slow)
        else:
            self.slow_ema = self.calculate_ema(list_item_slow, self.slow_ema)


        current_Value = self.fast_ema - self.slow_ema

        return current_Value