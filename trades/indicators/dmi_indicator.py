import indicator_settings as ids
import statistics as stats
from collections import deque
from decimal import Decimal

class DirectionalMovementIndexIndicator():


    def __init__(self, timeframe, timestamp, len, lensig, config):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.len = len
        self.lensig = lensig
        self.close_queue = deque(maxlen=2)
        self.high_queue = deque(maxlen=2)
        self.low_queue = deque(maxlen=2)
        self.tr_queue = deque(maxlen=self.len)
        self.atr = None
        self.plus = None
        self.minus = None
        self.plus_dm_queue = deque(maxlen=self.len)
        self.minus_dm_queue = deque(maxlen=self.len)
        self.adx = None
        self.ad_queue = deque(maxlen=self.lensig)
        self.current_value = None
        self.adx_queue = deque(maxlen=2)


        self.plus_value = None
        self.minus_value = None

        self.config = config

        self.long_condition = False
        self.short_condition = False

        lens = [self.len, self.lensig]
        self.max_len = max(lens) * 2
        self.warmed_up = False

    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.high_queue.appendleft(high)
        self.low_queue.appendleft(low)
        self.close_queue.appendleft(close)
        if len(self.high_queue) == 2 and len(self.low_queue) == 2 and len(self.close_queue) == 2:
            up = self.high_queue[0] - self.high_queue[1]
            down = -(self.low_queue[0] - self.low_queue[1])
            first_tr = high - low
            second_tr = abs(high - self.close_queue[1])
            third_tr = abs(low - self.close_queue[1])
            tr_list = [first_tr, second_tr, third_tr]
            tr = max(tr_list)
            self.tr_queue.appendleft(tr)
            if len(self.tr_queue) == self.len:
                self.atr = self.calculate_rma(self.tr_queue, len(self.tr_queue), self.atr)

                if up > down and up > 0:
                    self.plus_dm_queue.appendleft(up)
                else:
                    self.plus_dm_queue.appendleft(0)
                if up < down and down > 0:
                    self.minus_dm_queue.appendleft(down)
                else:
                    self.minus_dm_queue.appendleft(0)

                if len(self.plus_dm_queue) == self.len and len(self.minus_dm_queue) == self.len:
                    self.plus = self.calculate_rma(self.plus_dm_queue, len(self.plus_dm_queue), self.plus)
                    self.minus = self.calculate_rma(self.minus_dm_queue, len(self.minus_dm_queue), self.minus)
                    plus = Decimal(self.plus * 100) / self.atr
                    minus = Decimal(self.minus * 100) / self.atr
                    self.plus_value = plus
                    self.minus_value = minus
                    sum = plus + minus

                    first_ad = abs(plus - minus)
                    if sum == 0:
                        second_ad = 1
                    else:
                        second_ad = sum
                    ad = first_ad / second_ad
                    self.ad_queue.appendleft(ad)

                    if len(self.ad_queue) == self.lensig:
                        self.adx = self.calculate_rma(self.ad_queue, len(self.ad_queue), self.adx)
                        self.current_value = Decimal(self.adx * 100)

                        self.adx_queue.appendleft(self.current_value)
                        if len(self.adx_queue) == 2:
                            self.check_conditions()


    def calculate_rma(self, list_item, length, current_value):
        alpha = Decimal(1/length)

        if current_value is None:
            current_value = self.calculate_sma(list_item)
        else:
            current_value = alpha * Decimal(list_item[0]) + (1 - alpha) * Decimal(current_value)
        return current_value

    def calculate_sma(self, list_item):
        current_value = Decimal(sum(list_item) / len(list_item))
        return current_value


    def calculate_ema(self, list_item, current_value):
        if current_value is None:
            current_value = Decimal(sum(list_item) / len(list_item))
            return current_value
        else:
            k = Decimal(2 / (len(list_item) + 1))
            current_value = Decimal(list_item[0]) * k + current_value * Decimal(1 - k)
            return current_value



    def check_conditions(self):

        long_conditions = []
        short_conditions = []

        if self.config["long"]["ADX_below"] is None or self.current_value < self.config["long"]["ADX_below"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)

        if self.config["long"]["ADX_above"] is None or self.current_value > self.config["long"]["ADX_above"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["DMI"] is None or self.config["long"]["DMI"] != "POSITIVE" or (self.config["long"]["DMI"] == "POSITIVE" and self.plus_value > self.minus_value):
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["DMI"] is None or self.config["long"]["DMI"] != "NEGATIVE" or (self.config["long"]["DMI"] == "NEGATIVE" and self.plus_value < self.minus_value):
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["ADX_direction"] is None or self.config["long"]["ADX_direction"] != "RISING" or (self.config["long"]["ADX_direction"] == "RISING" and self.adx_queue[0] > self.adx_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["ADX_direction"] is None or self.config["long"]["ADX_direction"] != "FALLING" or (self.config["long"]["ADX_direction"] == "FALLING" and self.adx_queue[0] < self.adx_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)


        if self.config["short"]["ADX_below"] is None or self.current_value < self.config["short"]["ADX_below"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["ADX_above"] is None or self.current_value > self.config["short"]["ADX_above"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["DMI"] is None or self.config["short"]["DMI"] != "POSITIVE" or (self.config["short"]["DMI"] == "POSITIVE" and self.plus_value > self.minus_value):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["DMI"] is None or self.config["short"]["DMI"] != "NEGATIVE" or  (self.config["short"]["DMI"] == "NEGATIVE" and self.plus_value < self.minus_value):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["ADX_direction"] is None or self.config["short"]["ADX_direction"] != "RISING" or (self.config["short"]["ADX_direction"] == "RISING" and self.adx_queue[0] > self.adx_queue[1]):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["ADX_direction"] is None or self.config["short"]["ADX_direction"] != "FALLING" or (self.config["short"]["ADX_direction"] == "FALLING" and self.adx_queue[0] < self.adx_queue[1]):
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

        #print(short_conditions)