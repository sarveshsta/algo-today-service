
from collections import deque
from .moving_averages import JurikMovingAverage, KaufmannMovingAverage
from .coral_indicator import CoralIndicator
from .vidya_indicator import VidyaIndicator
from .mcginley_indicator import McGinleyDynamicIndicator
from decimal import Decimal
from settings import general_settings as gbs


class BaseLine():



    def __init__(self, baseline):
        self.baseline = baseline
        self.current_value = None

        self.proximity = gbs.RETEST_PROXIMITY / 100

        self.value_queue = deque(maxlen=2)
        self.price_queue = deque(maxlen=2)

        self.long_retest_queue = deque(maxlen=2)
        self.short_retest_queue = deque(maxlen=2)

        self.long_retest_queue.appendleft(False)
        self.short_retest_queue.appendleft(False)
        self.long_retest_queue.appendleft(False)
        self.short_retest_queue.appendleft(False)
        self.high = None
        self.low = None

        self.long_condition = False
        self.short_condition = False

        self.bar_index = 0
        self.cross_ago = 0
        self.cross_ago_down = 0
        self.entry_after = gbs.ENTRY_AFTER_BASELINE_CROSS

    def calculate_value(self, open, high, low, close, volume, timestamp):
        self.high = high
        self.low = low
        self.bar_index += 1
        #print("HERE")
        self.price_queue.appendleft(close)
        self.baseline.calculate_value(open, high, low, close, volume, timestamp)
        if self.baseline.current_value is not None:
            self.current_value = self.baseline.current_value
            self.value_queue.appendleft(self.current_value)
            if len(self.value_queue) == 2:
                if self.price_queue[0] > self.value_queue[0] and self.price_queue[1] < self.value_queue[1]:
                    self.cross_ago = self.bar_index
                if self.price_queue[0] < self.value_queue[0] and self.price_queue[1] > self.value_queue[1]:
                    self.cross_ago_down = self.bar_index
                self.check_conditions()

    def check_conditions(self):

        long_conditions = []
        short_conditions = []
        #print(f"{self.price_queue} {self.value_queue} {self.bar_index} {self.cross_ago} {self.entry_after}")
        if gbs.ENTRY_ON_CROSS:
            if self.price_queue[0] > self.value_queue[0] and self.price_queue[1] < self.value_queue[1] or (self.entry_after == "UNLIMITED" and self.price_queue[0] > self.value_queue[0]) or (self.entry_after != "UNLIMITED" and self.entry_after >= (self.bar_index - self.cross_ago) and self.price_queue[0] > self.value_queue[0]):
                long_conditions.append(True)
            else:
                long_conditions.append(False)
            if self.price_queue[0] < self.value_queue[0] and self.price_queue[1] > self.value_queue[1] or (self.entry_after == "UNLIMITED" and self.price_queue[0] < self.value_queue[0]) or (self.entry_after != "UNLIMITED" and self.entry_after >= (self.bar_index - self.cross_ago_down) and self.price_queue[0] < self.value_queue[0]):
                short_conditions.append(True)
            else:
                short_conditions.append(False)


        if gbs.ENTRY_ON_RETEST:
            if self.price_queue[0] < (self.value_queue[0] * Decimal(self.proximity + 1)) and self.low <= self.value_queue[0] and self.price_queue[0] >= self.value_queue[0]:
                long_conditions.append(True)
                self.long_retest_queue.appendleft(True)
            else:
                self.long_retest_queue.appendleft(False)
            if self.price_queue[0] > (self.value_queue[0] * Decimal(self.proximity + 1)) and self.high >= self.value_queue[0] and self.price_queue[0] <= self.value_queue[0]:
                short_conditions.append(True)
                self.short_retest_queue.appendleft(True)
            else:
                self.short_retest_queue.appendleft(False)
        #print(long_conditions)
        if True in long_conditions and not False in long_conditions:
            self.long_condition = True
        else:
            self.long_condition = False

        if True in short_conditions and not False in short_conditions:
            self.short_condition = True
        else:
            self.short_condition = False