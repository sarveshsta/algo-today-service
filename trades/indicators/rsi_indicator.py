# import indicator_settings as ids
# from collections import deque
# from decimal import Decimal
# from .stdev_indicator import StandardDeviationIndicator
# from decimal import Decimal
# import pandas as pd



# class RSI():


#     def __init__(self, timeframe, timestamp, config,source, rsiLengthInput,rsiSourceInput,maTypeInput,maLengthInput,bbMultInput,showDivergence):
#         self.timeframe = timeframe
#         self.timestamp = timestamp
#         self.config = config
#         self.source = source
#         self.rsi_length = rsiLengthInput
#         self.rsi_source = rsiSourceInput 
#         self.ma_type = maTypeInput
#         self.ma_length = maLengthInput
#         self.bb_multiplier = bbMultInput
#         self.show_divergence = showDivergence        
    
#     def calculate_value(self, open, high, low, close, volume, timestamp):
#         if self.source == "CLOSE":
#             src = close
#         elif self.source == "OPEN":
#             src = open
#         elif self.source == "HIGH":
#             src = high
#         elif self.source == "LOW":
#             src = low
#         elif self.source == "HL2":
#             src = (high + low) / 2
#         elif self.source == "HLC3":
#             src = (high + low + close) / 3
#         elif self.source == "OHLC4":
#             src = (open + high + low + close) / 4
#         elif self.source == "HLCC4":
#             src = (high + low + close + close) / 4
#         else:
#             raise Exception(f"Selected incorrect Source Value for Laguerre RSI, {self.source} is incorrect")
#         self.basis = self.ma(src, self.length, self.ma_type)
#         self.up =
#         self.down =



# def check_conditions(self):
#     long_conditions = []
#     short_conditions = []

#     # Check conditions for long position
#     if self.config["long"]["below"] is None or self.rsi_queue[0] < self.config["long"]["below"]:
#         long_conditions.append(True)
#     else:
#         long_conditions.append(False)

#     if self.config["long"]["above"] is None or self.rsi_queue[0] > self.config["long"]["above"]:
#         long_conditions.append(True)
#     else:
#         long_conditions.append(False)

#     if self.config["long"]["cross_above"] is None or (self.rsi_queue[0] > self.config["long"]["cross_above"] and self.rsi_queue[1] <= self.config["long"]["cross_above"]):
#         long_conditions.append(True)
#     else:
#         long_conditions.append(False)

#     if self.config["long"]["cross_below"] is None or (self.rsi_queue[0] < self.config["long"]["cross_below"] and self.rsi_queue[1] >= self.config["long"]["cross_below"]):
#         long_conditions.append(True)
#     else:
#         long_conditions.append(False)

#     if not self.config["long"]["signal_up"] or self.rsi_queue[0] > self.rsi_queue[1]:
#         long_conditions.append(True)
#     else:
#         long_conditions.append(False)

#     if not self.config["long"]["signal_down"] or self.rsi_queue[0] < self.rsi_queue[1]:
#         long_conditions.append(True)
#     else:
#         long_conditions.append(False)

#     # Check conditions for short position
#     if self.config["short"]["below"] is None or self.rsi_queue[0] < self.config["short"]["below"]:
#         short_conditions.append(True)
#     else:
#         short_conditions.append(False)

#     if self.config["short"]["above"] is None or self.rsi_queue[0] > self.config["short"]["above"]:
#         short_conditions.append(True)
#     else:
#         short_conditions.append(False)

#     if self.config["short"]["cross_above"] is None or (self.rsi_queue[0] > self.config["short"]["cross_above"] and self.rsi_queue[1] <= self.config["short"]["cross_above"]):
#         short_conditions.append(True)
#     else:
#         short_conditions.append(False)

#     if self.config["short"]["cross_below"] is None or (self.rsi_queue[0] < self.config["short"]["cross_below"] and self.rsi_queue[1] >= self.config["short"]["cross_below"]):
#         short_conditions.append(True)
#     else:
#         short_conditions.append(False)

#     if not self.config["short"]["signal_up"] or self.rsi_queue[0] > self.rsi_queue[1]:
#         short_conditions.append(True)
#     else:
#         short_conditions.append(False)

#     if not self.config["short"]["signal_down"] or self.rsi_queue[0] < self.rsi_queue[1]:  
#         short_conditions.append(True)
#     else:
#         short_conditions.append(False)

#     # Determine overall conditions for long and short
#     if all(long_conditions):
#         self.long_condition = True
#     else:
#         self.long_condition = False

#     if all(short_conditions):
#         self.short_condition = True
#     else:
#         self.short_condition = False












# # from collections import deque

# # class RSIIndicator():

# #     def __init__(self, period, config=None):
# #         self.period = period
# #         self.gains_queue = deque(maxlen=self.period)
# #         self.losses_queue = deque(maxlen=self.period)
# #         self.current_rsi = None
# #         self.config = config
# #         self.long_exit = False
# #         self.short_exit = False

# #     def calculate_value(self, close, prev_close, timestamp):
# #         gain = 0
# #         loss = 0

# #         if prev_close is not None:
# #             delta = close - prev_close

# #             if delta > 0:
# #                 gain = delta
# #             else:
# #                 loss = -delta

# #             self.gains_queue.appendleft(gain)
# #             self.losses_queue.appendleft(loss)

# #         if len(self.gains_queue) == self.period and len(self.losses_queue) == self.period:
# #             avg_gain = sum(self.gains_queue) / self.period
# #             avg_loss = sum(self.losses_queue) / self.period

# #             if avg_loss == 0:
# #                 self.current_rsi = 100
# #             else:
# #                 rs = avg_gain / avg_loss
# #                 self.current_rsi = 100 - (100 / (1 + rs))

# #             if self.config is not None:
# #                 self.check_conditions()

# #     def check_conditions(self):
# #         long_conditions = []
# #         short_conditions = []

# #         if self.config["long"]["oversold_level"] is None or self.current_rsi <= self.config["long"]["oversold_level"]:
# #             long_conditions.append(True)
# #         else:
# #             long_conditions.append(False)

# #         if self.config["long"]["overbought_level"] is None or self.current_rsi >= self.config["long"]["overbought_level"]:
# #             long_conditions.append(True)
# #         else:
# #             long_conditions.append(False)

# #         if self.config["short"]["oversold_level"] is None or self.current_rsi <= self.config["short"]["oversold_level"]:
# #             short_conditions.append(True)
# #         else:
# #             short_conditions.append(False)

# #         if self.config["short"]["overbought_level"] is None or self.current_rsi >= self.config["short"]["overbought_level"]:
# #             short_conditions.append(True)
# #         else:
# #             short_conditions.append(False)

# #         if True in long_conditions and not False in long_conditions:
# #             self.long_exit = True
# #         else:
# #             self.long_exit = False

# #         if True in short_conditions and not False in short_conditions:
# #             self.short_exit = True
# #         else:
# #             self.short_exit = False
