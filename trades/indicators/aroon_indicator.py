import indicator_settings as ids
import statistics as stats
from collections import deque
from itertools import islice
import math

class AroonIndicator():


    def __init__(self, timeframe, timestamp, length, config):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.length = length

        self.timeframe = timeframe
        self.timestamp = timestamp



        self.high_queue = deque(maxlen=self.length)
        self.low_queue = deque(maxlen=self.length)

        self.upper = None
        self.lower = None

        self.upper_queue = deque(maxlen=2)
        self.lower_queue = deque(maxlen=2)

        self.config = config

        self.current_value = None

        self.long_condition = False
        self.short_condition = False

        self.max_len = self.length * 2
        self.warmed_up = False


    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.high_queue.appendleft(high)
        self.low_queue.appendleft(low)

        if len(self.high_queue) == self.length and len(self.low_queue) == self.length:
            # Extract the deque values into lists
            days_since_high = self.length - self.high_queue.index(max(self.high_queue))
            days_since_low = self.length - self.low_queue.index(min(self.low_queue))

            # Calculate the Aroon-Up and Aroon-Down lines
            self.upper = ((days_since_high) / 14) * 100
            self.lower = ((days_since_low) / 14) * 100

            self.upper_queue.appendleft(self.upper)
            self.lower_queue.appendleft(self.lower)
            self.current_value = self.upper
            if len(self.upper_queue) == 2 and len(self.lower_queue) == 2:
                self.check_conditions()

    def check_conditions(self):
        long_conditions = []
        short_conditions = []
        #print(f"{self.upper_queue} {self.lower_queue}")
        if self.config["long"]["aroon_cross"] is None or (self.config["long"]["aroon_cross"] == "POSITIVE" and self.upper_queue[0] > self.lower_queue[0] and self.upper_queue[1] < self.lower_queue[1]) or (self.config["long"]["aroon_cross"] == "NEGATIVE" and self.upper_queue[0] < self.lower_queue[0] and self.upper_queue[1] > self.lower_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["aroon_up_above"] is None or self.upper >self.config["long"]["aroon_up_above"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["aroon_up_below"] is None or self.upper < self.config["long"]["aroon_up_below"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["aroon_down_above"] is None or self.lower > self.config["long"]["aroon_down_above"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["aroon_down_below"] is None or self.lower < self.config["long"]["aroon_down_below"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["aroon_up_direction"] is None or (self.config["long"]["aroon_up_direction"] == "UP" and self.upper_queue[0] > self.upper_queue[1]) or (self.config["long"]["aroon_up_direction"] == "DOWN" and self.upper_queue[0] < self.upper_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["aroon_down_direction"] is None or (self.config["long"]["aroon_down_direction"] == "UP" and self.lower_queue[0] > self.lower_queue[1]) or (self.config["long"]["aroon_down_direction"] == "DOWN" and self.lower_queue[0] < self.lower_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)


        if self.config["short"]["aroon_cross"] is None or (self.config["short"]["aroon_cross"] == "POSITIVE" and self.upper_queue[0] > self.lower_queue[0] and self.upper_queue[1] < self.lower_queue[1]) or (self.config["short"]["aroon_cross"] == "NEGATIVE" and self.upper_queue[0] < self.lower_queue[0] and self.upper_queue[1] > self.lower_queue[1]):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["aroon_up_above"] is None or self.upper > self.config["short"]["aroon_up_above"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["aroon_up_below"] is None or self.upper < self.config["short"]["aroon_up_below"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["aroon_down_above"] is None or self.lower > self.config["short"]["aroon_down_above"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["aroon_down_below"] is None or self.lower < self.config["short"]["aroon_down_below"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["aroon_up_direction"] is None or (self.config["short"]["aroon_up_direction"] == "UP" and self.upper_queue[0] > self.upper_queue[1]) or (self.config["short"]["aroon_up_direction"] == "DOWN" and self.upper_queue[0] < self.upper_queue[1]):
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if self.config["short"]["aroon_down_direction"] is None or (self.config["short"]["aroon_down_direction"] == "UP" and self.lower_queue[0] > self.lower_queue[1]) or (self.config["short"]["aroon_down_direction"] == "DOWN" and self.lower_queue[0] < self.lower_queue[1]):
            short_conditions.append(True)
        else:
            short_conditions.append(False)


        #print(long_conditions)

        if True in long_conditions and not False in long_conditions:
            self.long_condition = True
        else:
            self.long_condition = False

        if True in short_conditions and not False in short_conditions:
            self.short_condition = True
        else:
            self.short_condition = False