import indicator_settings as ids
from collections import deque
from decimal import Decimal



class CoralIndicator():


    def __init__(self, timeframe, timestamp, smoothing_period, constant_d, ribbon_mode, config):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.smoothing_period = smoothing_period
        self.constant_d = Decimal(constant_d)
        self.ribbon_mode = ribbon_mode
        self.is_ready = False
        self.i1 = 0
        self.i2 = 0
        self.i3 = 0
        self.i4 = 0
        self.i5 = 0
        self.i6 = 0
        self.previous_bfr = 0
        self.color = None

        self.bfr_queue = deque(maxlen=2)

        self.current_value = None

        self.config = config

        self.long_condition = False
        self.short_condition = False

        lens = [self.smoothing_period]
        self.max_len = max(lens) * 2
        self.warmed_up = False
        self.value_queue = deque(maxlen=2)
        self.slope = None

    def calculate_value(self, open, high, low, close, volume, timestamp):
        di = Decimal((self.smoothing_period - 1) / 2 + 1)
        c1 = Decimal(2 / (di + 1))
        c2 = Decimal(1 - c1)
        c3 = Decimal(3 * (self.constant_d * self.constant_d + self.constant_d * self.constant_d * self.constant_d))
        c4 = Decimal(-3 * (2 * self.constant_d * self.constant_d + self.constant_d + self.constant_d * self.constant_d * self.constant_d))
        c5 = Decimal(3 * self.constant_d + 1 + self.constant_d * self.constant_d * self.constant_d + 3 * self.constant_d * self.constant_d)
        self.i1 = c1 * close + c2 * self.i1
        self.i2 = c1 * self.i1 + c2 * self.i2
        self.i3 = c1 * self.i2 + c2 * self.i3
        self.i4 = c1 * self.i3 + c2 * self.i4
        self.i5 = c1 * self.i4 + c2 * self.i5
        self.i6 = c1 * self.i5 + c2 * self.i6

        bfr = -self.constant_d * self.constant_d * self.constant_d  * self.i6 + c3 * (self.i5) + c4 * (self.i4) + c5 * (self.i3)
        #print(f"BFR {bfr}")
        self.bfr_queue.appendleft(bfr)
        if len(self.bfr_queue) == 2:
            if bfr > self.bfr_queue[1]:
                self.color = "GREEN"
            elif bfr < self.bfr_queue[1]:
                self.color = "RED"
            else:
                self.color = "BLUE"


            self.current_value = bfr
            self.value_queue.appendleft(self.current_value)
            if len(self.value_queue) == 2:
                x1, y1 = 0, self.value_queue[1]
                x2, y2 = 1, self.value_queue[0]
                self.slope = (y2 - y1) / (x2 - x1)
            if self.config is not None:
                self.check_conditions()

    def check_conditions(self):
        long_conditions = []
        short_conditions = []
        #print(self.color)
        if len(self.config["long"]["Color"]) == 0 or self.color in self.config["long"]["Color"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if len(self.config["long"]["direction"]) == 0 or ("RISING" in self.config["long"]["direction"]  and self.bfr_queue[0] > self.bfr_queue[1]) or ("FALLING" in self.config["long"]["direction"] and self.bfr_queue[0] < self.bfr_queue[1]) or ("FLAT" in self.config["long"]["direction"] and self.bfr_queue[0] == self.bfr_queue[1]):
            long_conditions.append(True)
        else:
            long_conditions.append(False)


        if len(self.config["short"]["Color"]) == 0 or self.color in self.config["short"]["Color"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if len(self.config["short"]["direction"]) == 0 or ("RISING" in self.config["short"]["direction"] and self.bfr_queue[0] > self.bfr_queue[1]) or ("FALLING" in self.config["short"]["direction"] and self.bfr_queue[0] < self.bfr_queue[1]) or ("FLAT" in self.config["short"]["direction"] and self.bfr_queue[0] == self.bfr_queue[1]):
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
