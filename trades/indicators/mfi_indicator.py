import indicator_settings as ids
import statistics as stats
from collections import deque
from itertools import islice
import math
import datetime

class MoneyFlowIndexIndicator():


    def __init__(self, timeframe, timestamp, length, config):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.length = length

        self.source_queue = deque(maxlen=2)
        self.upper_queue = deque(maxlen=self.length)
        self.lower_queue = deque(maxlen=self.length)

        self.value_queue = deque(maxlen=2)

        self.config = config

        self.long_condition = False
        self.short_condition = False


        lens = [self.length]
        self.max_len = max(lens) * 2
        self.current_value = None
        self.warmed_up = False

    def calculate_value(self, open, high, low, close, volume, timestamp):
        src = (high + low + close) / 3
        self.source_queue.appendleft(src)

        if len(self.source_queue) == 2:
            self.current_value = self.calculate_mfi(self.source_queue, volume)
            if self.current_value is not None:
                self.value_queue.appendleft(self.current_value)
            if len(self.value_queue) == 2 and self.current_value is not None:
                #print(f"MFI {self.current_value} {datetime.datetime.now()} {close} {volume} {timestamp}")
                self.check_conditions()

    def check_conditions(self):
        #print(f"{self.current_value} {self.value_queue}")
        long_conditions = []
        short_conditions = []
        if self.config["long"]["below"] is None or self.current_value < self.config["long"]["below"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["above"] is None or self.current_value > self.config["long"]["above"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["cross_above"] is None or (self.value_queue[0] > self.config["long"]["cross_above"] and self.value_queue[1] < self.config["long"]["cross_above"]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["cross_below"] is None or (self.value_queue[0] < self.config["long"]["cross_below"] and self.value_queue[1] > self.config["long"]["cross_below"]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["signal_line_direction"] is None or (self.config["long"]["signal_line_direction"] == "UP" and self.value_queue[0] > self.value_queue[1]) or (self.config["long"]["signal_line_direction"] == "DOWN" and self.value_queue[0] < self.value_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)



        if self.config["short"]["below"] is None or self.current_value < self.config["short"]["below"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["above"] is None or self.current_value > self.config["short"]["above"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["cross_above"] is None or (self.value_queue[0] > self.config["short"]["cross_above"] and self.value_queue[1] < self.config["short"]["cross_above"]):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["cross_below"] is None or (self.value_queue[0] < self.config["short"]["cross_below"] and self.value_queue[1] > self.config["short"]["cross_below"]):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["signal_line_direction"] is None or (self.config["short"]["signal_line_direction"] == "UP" and self.value_queue[0] > self.value_queue[1]) or (self.config["short"]["signal_line_direction"] == "DOWN" and self.value_queue[0] < self.value_queue[1]):
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

        #print(long_conditions)


    def calculate_mfi(self, list_item, volume):
        change = volume * (list_item[0] - list_item[1])

        if change <= 0:
            upper_step = 0 * volume
        else:
            upper_step = list_item[0] * volume
        if change > 0:
            lower_step = 0 * volume
        else:
            lower_step = list_item[0] * volume

        self.upper_queue.appendleft(upper_step)
        self.lower_queue.appendleft(lower_step)

        current_value = None

        if len(self.upper_queue) == self.length and len(self.lower_queue) == self.length:
            upper = sum(self.upper_queue)
            lower = sum(self.lower_queue)
            upper = round(upper, 2)
            lower = round(lower, 2)

            if upper != 0 and lower != 0:
                current_value = 100 - (100 / (1 + (upper / lower)))
            else:
                current_value = self.current_value


        return current_value
