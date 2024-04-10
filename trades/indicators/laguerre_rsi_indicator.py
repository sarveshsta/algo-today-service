import indicator_settings as ids
import statistics as stats
from collections import deque
from itertools import islice
import math
from decimal import Decimal

class LaguerreRsiIndicator():


    def __init__(self, timeframe, timestamp, alpha, crossovers, apply_fractals, fractal_length, normalization, source, config):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.alpha = Decimal(alpha)
        self.crossovers = crossovers
        self.apply_fractals = apply_fractals
        self.fractal_length = fractal_length
        self.normalization = normalization
        self.source = source
        self.config = config
        #print(f"{alpha} {apply_fractals} {fractal_length} {normalization}")
        self.close_queue = deque(maxlen=2)
        self.high_queue = deque(maxlen=self.fractal_length)
        self.low_queue = deque(maxlen=self.fractal_length)

        self.L0 = 0
        self.L0_queue = deque(maxlen=2)
        self.L0_queue.appendleft(self.L0)
        self.L0_queue.appendleft(self.L0)

        self.L1 = 0
        self.L1_queue = deque(maxlen=2)
        self.L1_queue.appendleft(self.L1)
        self.L1_queue.appendleft(self.L1)

        self.L2 = 0
        self.L2_queue = deque(maxlen=2)
        self.L2_queue.appendleft(self.L2)
        self.L2_queue.appendleft(self.L2)

        self.L3 = 0
        self.L3_queue = deque(maxlen=2)
        self.L3_queue.appendleft(self.L3)
        self.L3_queue.appendleft(self.L3)

        self.CU = 0
        self.CD = 0

        self.lrsi_color = ""
        self.fe_alpha = None

        self.lrsi_queue = deque(maxlen=2)
        self.ob_queue = deque(maxlen=2)
        self.os_queue = deque(maxlen=2)

        self.overbought_cross = False
        self.oversold_cross = False

        lens = [self.fractal_length]
        self.max_len = max(lens) * 2
        self.warmed_up = False

        self.current_value = None

        self.long_condition = False
        self.short_condition = False

    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.close_queue.appendleft(close)
        self.high_queue.appendleft(high)
        self.low_queue.appendleft(low)
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
        if len(self.close_queue) == 2:
            OC = (open + self.close_queue[1]) / 2
            HC = max(high, self.close_queue[1])
            LC = min(low, self.close_queue[1])

            fe_src = (OC + HC + LC + close) / 4


            if len(self.high_queue) == self.fractal_length and len(self.low_queue) == self.fractal_length:
                x = (HC - LC)
                y = ((HC - LC) / ((max(self.high_queue) - min(self.low_queue))))
                z = self.fractal_length
                q = [y, z]
                fe_alpha = Decimal((math.log(sum(q))) / math.log(self.fractal_length))

                if self.apply_fractals:
                    lrsi_is_alpha = fe_alpha
                else:
                    lrsi_is_alpha = self.alpha


                if self.apply_fractals:
                    self.L0 = (lrsi_is_alpha * (fe_src) + (1 - lrsi_is_alpha) * self.L0)
                else:
                    self.L0 = (lrsi_is_alpha * (src) + (1 - lrsi_is_alpha) * self.L0)
                self.L0_queue.appendleft(self.L0)

                self.L1 = -(1 - lrsi_is_alpha) * self.L0 + self.L0_queue[1] + (1 - lrsi_is_alpha) * self.L1
                self.L1_queue.appendleft(self.L1)

                self.L2 = -(1 - lrsi_is_alpha) * self.L1 + self.L1_queue[1] + (1 - lrsi_is_alpha) * self.L2
                self.L2_queue.appendleft(self.L2)

                self.L3 = -(1 - lrsi_is_alpha) * self.L2 + self.L2_queue[1] + (1 - lrsi_is_alpha) * self.L3
                self.L3_queue.appendleft(self.L3)

                self.CU = (self.L0 - self.L1 if self.L0 >= self.L1 else 0) + (self.L1 - self.L2 if self.L1 >= self.L2 else 0) + (self.L2 - self.L3 if self.L2 >= self.L3 else 0)

                self.CD = (0 if self.L0 >= self.L1 else self.L1 - self.L0) + (0 if self.L1 >= self.L2 else self.L2 - self.L1) + (0 if self.L2 >= self.L3 else self.L3 - self.L2)

                if self.CU + self.CD != 0:
                    if self.normalization:
                        lrsi = 100 * self.CU / (self.CU + self.CD)
                    else:
                        lrsi = self.CU / (self.CU + self.CD)
                else:
                    lrsi = 0

                if self.normalization:
                    mult = 100
                else:
                    mult = 1

                ob = 0.8 * mult
                middle = 0.5 * mult
                os = 0.2 * mult

                if lrsi > ob:
                    self.lrsi_color = "BLUE"
                elif lrsi < os:
                    self.lrsi_color = "RED"
                else:
                    self.lrsi_color = "GREEN"

                if self.apply_fractals and self.normalization:
                    self.fe_alpha = 100 * fe_alpha
                else:
                    self.fe_alpha = fe_alpha

                self.lrsi_queue.appendleft(lrsi)
                self.ob_queue.appendleft(ob)
                self.os_queue.appendleft(os)
                self.current_value = lrsi
                if len(self.lrsi_queue) == 2 and len(self.ob_queue) == 2 and len(self.os_queue) == 2:
                    lrsi_1 = self.lrsi_queue[0]
                    lrsi_2 = self.lrsi_queue[1]

                    ob_1 = self.ob_queue[0]
                    ob_2 = self.ob_queue[1]

                    os_1 = self.os_queue[0]
                    os_2 = self.os_queue[1]
                    #print(self.lrsi_queue)
                    if lrsi_2 > ob_2 and lrsi_1 < ob_1:
                        self.overbought_cross = True
                    if lrsi_2 < os_2 and lrsi_1 > os_1:
                        self.oversold_cross = True
                    self.check_conditions()

    def check_conditions(self):
        long_conditions = []
        short_conditions = []
        # Check conditions for long position
        if self.config["long"]["below"] is None or self.lrsi_queue[0] < self.config["long"]["below"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)

        if self.config["long"]["above"] is None or self.lrsi_queue[0] > self.config["long"]["above"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)

        if self.config["long"]["cross_above"] is None or self.lrsi_queue[0] > self.config["long"]["cross_above"] and self.lrsi_queue[1] <= self.config["long"]["cross_above"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if self.config["long"]["cross_below"] is None or  self.lrsi_queue[0] < self.config["long"]["cross_below"] and self.lrsi_queue[1] >= self.config["long"]["cross_below"]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if not self.config["long"]["signal_up"] or self.lrsi_queue[0] > self.lrsi_queue[1]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)
        if not self.config["long"]["signal_down"] or self.lrsi_queue[0] < self.lrsi_queue[1]:
            long_conditions.append(True)
        else:
            long_conditions.append(False)

        # Check conditions for short position
        if self.config["short"]["below"] is None or self.lrsi_queue[0] < self.config["short"]["below"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)

        if self.config["short"]["above"] is None or self.lrsi_queue[0] > self.config["short"]["above"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)

        if self.config["short"]["cross_above"] is None or self.lrsi_queue[0] > self.config["short"]["cross_above"] and self.lrsi_queue[1] <= self.config["short"]["cross_above"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)

        if self.config["short"]["cross_below"] is None or self.lrsi_queue[0] < self.config["short"]["cross_below"] and self.lrsi_queue[1] >= self.config["short"]["cross_below"]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if not self.config["short"]["signal_up"] or self.lrsi_queue[0] > self.lrsi_queue[1]:
            short_conditions.append(True)
        else:
            short_conditions.append(False)
        if not self.config["short"]["signal_down"] or self.lrsi_queue[0] < self.lrsi_queue[1]:  # LRSI signal is pointing down for short position  # Apply corresponding logic here
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

