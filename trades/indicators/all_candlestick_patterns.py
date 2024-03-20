import indicator_settings as ids
import statistics as stats
from collections import deque
from itertools import islice
import math

class AllCandlestickPatterns():


    def __init__(self, timeframe, timestamp):
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.C_DownTrend = True
        self.C_UpTrend = True
        self.trendRule = ids.CS_DETECT_TREND_BASED_ON

        self.C_Len = 14
        self.C_Shdadow_Percent = 5
        self.C_ShadowEqualsPercent = 100
        self.C_DojiBodyPercent = 5
        self.C_Factor = 2

        self.open_queue = deque(maxlen=5)
        self.close_queue = deque(maxlen=200)
        self.high_queue = deque(maxlen=5)
        self.low_queue = deque(maxlen=5)
        self.C_Body_queue = deque(maxlen=self.C_Len)
        self.C_BodyAvg = None
        self.C_BodyHi_queue = deque(maxlen=5)
        self.C_BodyLo_queue = deque(maxlen=5)

        self.tr = None
        self.tr_queue = deque(maxlen=30)
        self.atr = None

        lens = [self.C_Len, 30, 200]
        self.max_len = max(lens) * 2

        self.warmed_up = False

        self.CandleType = ids.CS_PATTERN_TYPE


        self.label_color_bullish = "BLUE"
        self.label_color_bearish = "RED"
        self.label_color_neutral = "GRAY"
        self.AbandonedBabyInput = ids.CS_ABANDONED_BABY
        self.DarkCloudCoverInput = ids.CS_DARK_CLOUD_COVER
        self.DojiInput = ids.CS_DOJI
        self.DojiStarInput = ids.CS_DOJI_STAR
        self.DownSideTasukiGapInput = ids.CS_DOWNSIDE_TASUKI_GAP
        self.DragonflyDojiInput = ids.CS_DRAGONFLY_DOJI
        self.EngulfingInput = ids.CS_ENGULFING
        self.EveningDojiStarInput = ids.CS_EVENING_DOJI_STAR
        self.EveningStarInput = ids.CS_EVENING_STAR
        self.FallingThreeMethodsInput = ids.CS_FALLING_THREE_METHODS
        self.FallingWindowInput = ids.CS_FALLING_WINDOW
        self.GravestoneDojiInput = ids.CS_GRAVESTONE_DOJI
        self.HammerInput = ids.CS_HAMMER
        self.HangingManInput = ids.CS_HANGING_MAN
        self.HaramiCrossInput = ids.CS_HARAMI_CROSS
        self.HaramiInput = ids.CS_HARAMI
        self.InvertedHammerInput = ids.CS_INVERTED_HAMMER
        self.KickingInput = ids.CS_KICKING
        self.LongLowerShadowInput = ids.CS_LONG_LOWER_SHADOW
        self.LongUpperShadowInput = ids.CS_LONG_UPPER_SHADOW
        self.MarubozuBlackInput = ids.CS_MARUBOZU_BLACK
        self.MarubozuWhiteInput = ids.CS_MARUBOZU_WHITE
        self.MorningDojiStarInput = ids.CS_MORNING_DOJI_STAR
        self.MorningStarInput = ids.CS_MORNING_STAR
        self.OnNeckInput = ids.CS_ON_NECK
        self.PiercingInput = ids.CS_PIERCING
        self.RisingThreeMethodsInput = ids.CS_RISING_THREE_METHODS
        self.RisingWindowInput = ids.CS_RISING_WINDOW
        self.ShootingStarInput = ids.CS_SHOOTING_STAR
        self.SpinningTopBlackInput = ids.CS_SPINNING_TOP_BLACK
        self.SpinningTopWhiteInput = ids.CS_SPINNING_TOP_WHITE
        self.ThreeBlackCrowsInput = ids.CS_THREE_BLACK_CROWS
        self.ThreeWhiteSoldiersInput = ids.CS_THREE_WHITE_SOLDIERS
        self.TriStarInput = ids.CS_TRI_STAR
        self.TweezerBottomInput = ids.CS_TWEEZER_BOTTOM
        self.TweezerTopInput = ids.CS_TWEEZER_TOP
        self.UpsideTasukiGapInput = ids.CS_UPSIDE_TASUKI_GAP

        self.C_BlackBody_queue = deque(maxlen=5)
        self.C_WhiteBody_queue = deque(maxlen=5)
        self.C_LongBody_queue = deque(maxlen=5)
        self.C_SmallBody_queue = deque(maxlen=5)

        self.C_UpTrend_queue = deque(maxlen=5)
        self.C_Range_queue = deque(maxlen=5)
        self.C_DownTrend_queue = deque(maxlen=5)
        self.C_BodyMiddle_queue = deque(maxlen=5)
        self.C_IsDojiBody_queue = deque(maxlen=5)
        self.C_3WSld_HaveNotUpShadow_queue = deque(maxlen=5)
        self.C_3BCrw_HaveNotDnShadow_queue = deque(maxlen=5)
        self.C_Doji_queue = deque(maxlen=5)
        self.C_BodyGapUpBullish_queue = deque(maxlen=5)
        self.C_BodyGapDnBullish_queue = deque(maxlen=5)
        self.C_BodyGapUp_queue = deque(maxlen=5)
        self.C_BodyGapDn_queue = deque(maxlen=5)
        self.C_MarubozuBlackBullish_queue = deque(maxlen=5)
        self.C_MarubozuWhiteBullishKicking_queue = deque(maxlen=5)
        self.C_MarubozuWhiteBearish_queue = deque(maxlen=5)


        self.C_OnNeckBearish = False
        self.C_RisingWindowBullish = False
        self.C_FallingWindowBearish = False
        self.C_FallingThreeMethodsBearish = False
        self.C_RisingThreeMethodsBullish = False
        self.C_TweezerTopBearish = False
        self.C_TweezerBottomBullish = False
        self.C_DownsideTasukiGapBearish = False
        self.C_UpsideTasukiGapBullish = False
        self.C_EveningDojiStarBearish = False
        self.C_DojiStarBearish = False
        self.C_DojiStarBullish = False
        self.C_MorningDojiStarBullish = False
        self.C_PiercingBullish = False
        self.C_HammerBullish = False
        self.C_HangingManBearish = False
        self.C_ShootingStarBearish = False
        self.C_InvertedHammerBullish = False
        self.C_MorningStarBullish = False
        self.C_EveningStarBearish = False
        self.C_MarubozuWhiteBullish = False
        self.C_MarubozuBlackBearish = False
        self.C_DragonflyDoji = False
        self.C_GravestoneDojiOne = False
        self.C_GravestoneDojiBearish = False
        self.C_DragonflyDojiBullish = False
        self.C_HaramiCrossBullish = False
        self.C_HaramiCrossBearish = False
        self.C_HaramiBullish = False
        self.C_HaramiBearish = False
        self.C_LongLowerShadowBullish = False
        self.C_LongUpperShadowBearish = False
        self.C_IsSpinningTopWhite = False
        self.C_SpinningTopWhite = False
        self.C_IsSpinningTop = False
        self.C_SpinningTopBlack = False
        self.C_ThreeWhiteSoldiersBullish = False
        self.C_ThreeBlackCrowsBearish = False
        self.C_EngulfingBullish = False
        self.C_EngulfingBearish = False
        self.C_AbandonedBabyBullish = False
        self.C_TriStarBullish = False
        self.C_TriStarBearish = False
        self.C_KickingBullish = False
        self.C_KickingBearish = False

        self.bar_index = 0

        self.ttBearishOnNeck_list = []
        self.ttBullishRisingWindow_list = []
        self.ttBearishFallingWindow_list = []
        self.ttBearishFallingThreeMethods_list = []
        self.ttBullishRisingThreeMethods_list = []
        self.ttBearishTweezerTop_list = []
        self.ttBullishTweezerBottom_list = []
        self.ttBearishDarkCloudCover_list = []
        self.ttBearishDownsideTasukiGap_list = []
        self.ttBullishUpsideTasukiGap_list = []
        self.ttBearishEveningDojiStar_list = []
        self.ttBullishDojiStar_list = []
        self.ttBullishMorningDojiStar_list = []
        self.ttBullishPiercing_list = []
        self.ttBullishPiercing_list = []
        self.ttBearishHangingMan_list = []
        self.ttBearishShootingStar_list = []
        self.ttBullishInvertedHammer_list = []
        self.ttBullishMorningStar_list = []
        self.ttBearishEveningStar_list = []
        self.ttBullishMarubozuWhite_list = []
        self.ttBearishMarubozuBlack_list = []
        self.ttDoji_list = []
        self.ttBearishGravestoneDoji_list = []
        self.ttBullishDragonflyDoji_list = []
        self.ttBullishHaramiCross_list = []
        self.ttBearishHaramiCross_list = []
        self.ttBullishHarami_list = []
        self.ttBearishHarami_list = []
        self.ttBullishLongLowerShadow_list = []
        self.ttBearishLongUpperShadow_list = []
        self.ttSpinningTopWhite_list = []
        self.ttSpinningTopBlack_list = []
        self.ttBullishThreeWhiteSoldiers_list = []
        self.ttBearishThreeBlackCrows_list = []
        self.ttBullishEngulfing_list = []
        self.ttBearishEngulfing_list = []
        self.ttBullishAbandonedBaby_list = []
        self.ttBearishAbandonedBaby_list = []
        self.ttBullishTriStar_list = []
        self.ttBearishTriStar_list = []
        self.ttBullishKicking_list = []
        self.ttBearishKicking_list = []
        self.ttAllCandlestickPatterns_list = []
        self.ttBullishHammer_list = []


        self.current_candle = []


    def calculate_value(self, open, high, low, close, volume, timestamp):
        x = False
        if x:
            self.bar_index += 1

            self.open_queue.appendleft(open)
            self.close_queue.appendleft(close)
            self.high_queue.appendleft(high)
            self.low_queue.appendleft(low)
            hl2 = (high + low) / 2

            if len(self.close_queue) == 200:
                if self.trendRule == "SMA50":
                    priceAvg = self.calculate_sma(deque(islice(self.close_queue, 0, 49)))
                    self.C_DownTrend = True if close < priceAvg else False
                    self.C_UpTrend = True if close > priceAvg else False
                elif self.trendRule == "SMA50, SMA200":
                    sma200 = self.calculate_sma(self.close_queue)
                    sma50 = self.calculate_sma(deque(islice(self.close_queue, 0, 49)))
                    self.C_DownTrend = True if close < sma50 and sma50 < sma200 else False
                    self.C_UpTrend = True if close > sma50 and sma50 > sma200 else False

                self.C_UpTrend_queue.appendleft(self.C_UpTrend)
                self.C_DownTrend_queue.appendleft(self.C_DownTrend)

                C_BodyHi = max(close, open)
                C_BodyLo = min(close, open)
                self.C_BodyHi_queue.appendleft(C_BodyHi)
                self.C_BodyLo_queue.appendleft(C_BodyLo)
                C_Body = C_BodyHi - C_BodyLo
                self.C_Body_queue.appendleft(C_Body)

                if len(self.C_Body_queue) == self.C_Len:
                    self.C_BodyAvg = self.calculate_ema(self.C_Body_queue, self.C_BodyAvg)
                    C_SmallBody = True if C_Body < self.C_BodyAvg else False
                    C_LongBody = True if C_Body > self.C_BodyAvg else False
                    C_UpShadow = high - C_BodyHi
                    C_DnShadow = C_BodyLo - low
                    C_HasUpShadow = True if C_UpShadow > self.C_Shdadow_Percent / 100 * C_Body else False
                    C_HasDnShadow = True if C_DnShadow > self.C_Shdadow_Percent / 100 * C_Body else False
                    C_WhiteBody = True if open < close else False
                    C_BlackBody = True if open > close else False
                    self.C_BlackBody_queue.appendleft(C_BlackBody)
                    self.C_WhiteBody_queue.appendleft(C_WhiteBody)
                    self.C_LongBody_queue.appendleft(C_LongBody)
                    self.C_SmallBody_queue.appendleft(C_SmallBody)
                    C_Range = high - low
                    self.C_Range_queue.appendleft(C_Range)
                    if len(self.C_BodyHi_queue) == 5 and len(self.C_BodyLo_queue) == 5:
                        C_IsInsideBar = True if self.C_BodyHi_queue[1] > C_BodyHi and self.C_BodyLo_queue[1] < C_BodyLo else False
                        C_BodyMiddle = C_Body / 2 + C_BodyLo
                        C_ShadowEquals = True if C_UpShadow == C_DnShadow or (abs(C_UpShadow - C_DnShadow) / C_DnShadow * 100) < self.C_ShadowEqualsPercent and (abs(C_DnShadow - C_UpShadow) / C_UpShadow * 100) < self.C_ShadowEqualsPercent else False
                        C_IsDojiBody = True if C_Range > 0 and C_Body <= C_Range * self.C_DojiBodyPercent / 100 else False
                        C_Doji = True if C_IsDojiBody and C_ShadowEquals else False
                        self.C_Doji_queue.appendleft(C_Doji)
                        self.C_BodyMiddle_queue.appendleft(C_BodyMiddle)
                        self.C_IsDojiBody_queue.appendleft(C_IsDojiBody)
                        self.tr = self.calculate_true_range(high, low, self.close_queue)
                        self.tr_queue.appendleft(self.tr)
                        if len(self.tr_queue) == 30:
                            self.atr = self.calculate_ema(self.tr_queue, self.atr)
                            patternLabelPosLow = low - (self.atr * 0.6)
                            patternLabelPosHigh = high + (self.atr * 0.6)

                            C_OnNeckBearishNumberOfCandles = 2
                            self.C_OnNeckBearish = False

                            if C_Doji:
                                self.current_candle.append("DOJI")
                            if C_SmallBody:
                                self.current_candle.append("SMALL_BODY")
                            if C_LongBody:
                                self.current_candle.append("LONG_BODY")
                            if C_UpShadow:
                                self.current_candle.append("UP_SHADOW")
                            if C_HasDnShadow:
                                self.current_candle.append("DOWN_SHADOW")
                            if C_WhiteBody:
                                self.current_candle.append("WHITE_SHADOW")
                            if C_BlackBody:
                                self.current_candle.append("BLACK_SHADOW")




                            if len(self.C_BlackBody_queue) == 5 and len(self.C_LongBody_queue) == 5:
                                if self.C_DownTrend and self.C_BlackBody_queue[1] and self.C_LongBody_queue[1] and C_WhiteBody and open < self.close_queue[1] and C_SmallBody and C_Range != 0 and abs(close - self.low_queue[1]) <= self.C_BodyAvg * 0.05:
                                    self.C_OnNeckBearish = True
                                if self.C_OnNeckBearish and self.OnNeckInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):
                                    ttBearishOnNeck = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                    self.ttBearishOnNeck_list.append(ttBearishOnNeck)
                                    self.current_candle.append("ttBearishOnNeck")

                                C_RisingWindowBullishNumberOfCandles = 2
                                self.C_RisingWindowBullish = False
                                if len(self.C_UpTrend_queue) == 5 and len(self.C_Range_queue) == 5:
                                    if self.C_UpTrend_queue[1] and (C_Range != 0 and self.C_Range_queue[1] != 0) and low > self.high_queue[1]:
                                        self.C_RisingWindowBullish = True
                                    if self.C_RisingWindowBullish and self.RisingWindowInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):
                                        ttBullishRisingWindow = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                        self.ttBullishRisingWindow_list.append(ttBullishRisingWindow)
                                        self.current_candle.append("ttBullishRisingWindow")

                                    C_FallingWindowBearishNumberOfCandles = 2
                                    self.C_FallingWindowBearish = False
                                    if len(self.C_DownTrend_queue) == 5:
                                        if self.C_DownTrend_queue[1] and (C_Range != 0 and self.C_Range_queue[1] != 0) and high < self.low_queue[1]:
                                            self.C_FallingWindowBearish = True
                                        if self.C_FallingWindowBearish and self.FallingWindowInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):
                                            ttBearishFallingWindow = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishFallingWindow_list.append(ttBearishFallingWindow)
                                            self.current_candle.append("ttBearishFallingWindow")

                                        C_FallingThreeMethodsBearishNumberOfCandles = 5
                                        self.C_FallingThreeMethodsBearish = False

                                        if self.C_DownTrend_queue[4] and (self.C_LongBody_queue[4] and self.C_WhiteBody_queue[4]) and (self.C_SmallBody_queue[3] and self.C_WhiteBody_queue[3] and self.open_queue[3] > self.low_queue[4] and self.close_queue[3] < self.high_queue[4]) and (self.C_SmallBody_queue[2] and self.C_WhiteBody_queue[2] and self.open_queue[2] > self.low_queue[4] and self.close_queue[2] < self.high_queue[4]) and (self.C_SmallBody_queue[1] and self.C_WhiteBody_queue[1] and self.open_queue[1] > self.low_queue[4] and self.close_queue[1] < self.high_queue[4]) and (C_LongBody and C_BlackBody and close < self.close_queue[4]):
                                            self.C_FallingThreeMethodsBearish = True
                                        if self.C_FallingThreeMethodsBearish  and self.FallingThreeMethodsInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):
                                            ttBearishFallingThreeMethods = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishFallingThreeMethods_list.append(ttBearishFallingThreeMethods)
                                            self.current_candle.append("ttBearishFallingThreeMethods")

                                        C_RisingThreeMethodsBullishNumberOfCandles = 5
                                        self.C_RisingThreeMethodsBullish = False

                                        if self.C_UpTrend_queue[4] and (self.C_LongBody_queue[4] and self.C_WhiteBody_queue[4]) and (self.C_SmallBody_queue[3] and self.C_BlackBody_queue[3] and self.open_queue[3] < self.high_queue[4] and self.close_queue[3] > self.low_queue[4]) and (self.C_SmallBody_queue[2] and self.C_BlackBody_queue[2] and self.open_queue[2] < self.high_queue[4] and self.close_queue[2] > self.low_queue[4]) and (self.C_SmallBody_queue[1] and self.C_BlackBody_queue[1] and self.open_queue[1] < self.high_queue[4] and self.close_queue[1] > self.low_queue[4]) and (C_LongBody and C_WhiteBody and close > self.close_queue[4]):
                                            self.C_RisingThreeMethodsBullish = True
                                        if self.C_RisingThreeMethodsBullish and self.RisingThreeMethodsInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):
                                            ttBullishRisingThreeMethods = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                            self.ttBullishRisingThreeMethods_list.append(ttBullishRisingThreeMethods)
                                            self.current_candle.append("ttBullishRisingThreeMethods")

                                        C_TweezerTopBearishNumberOfCandles = 2
                                        self.C_TweezerTopBearish = False

                                        if self.C_UpTrend_queue[1] and (not C_IsDojiBody or (C_HasUpShadow and C_HasDnShadow)) and abs(high - self.high_queue[1]) <= self.C_BodyAvg * 0.05 and self.C_WhiteBody_queue[1] and C_BlackBody and self.C_LongBody_queue[1]:
                                            self.C_TweezerTopBearish = True
                                        if self.C_TweezerTopBearish and self.TweezerTopInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):
                                            ttBearishTweezerTop = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishTweezerTop_list.append(ttBearishTweezerTop)
                                            self.current_candle.append("ttBearishTweezerTop")
                                        C_TweezerBottomBullishNumberOfCandles = 2
                                        self.C_TweezerBottomBullish = False

                                        if self.C_DownTrend_queue[1] and (not C_IsDojiBody or (C_HasUpShadow and C_HasDnShadow)) and abs(low - self.low_queue[1]) < self.C_BodyAvg * 0.05 and self.C_BlackBody_queue[1] and C_WhiteBody and self.C_LongBody_queue[1]:
                                            self.C_TweezerBottomBullish = True
                                        if self.C_TweezerBottomBullish and self.TweezerBottomInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):
                                            ttBullishTweezerBottom = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                            self.ttBullishTweezerBottom_list.append(ttBullishTweezerBottom)
                                            self.current_candle.append("ttBullishTweezerBottom")
                                        C_DarkCloudCoverBearishNumberOfCandles = 2
                                        self.C_DarkCloudCoverBearish = False


                                        if (self.C_UpTrend_queue[1] and self.C_WhiteBody_queue[1] and self.C_LongBody_queue[1]) and (C_BlackBody and open >= self.high_queue[1] and close < self.C_BodyMiddle_queue[1] and close > self.open_queue[1]):
                                            self.C_DarkCloudCoverBearish = True
                                        if self.C_DarkCloudCoverBearish and self.DarkCloudCoverInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):
                                            ttBearishDarkCloudCover = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishDarkCloudCover_list.append(ttBearishDarkCloudCover)
                                            self.current_candle.append("ttBearishDarkCloudCover")
                                        C_DownsideTasukiGapBearishNumberOfCandles = 3
                                        self.C_DownsideTasukiGapBearish = False

                                        if self.C_LongBody_queue[2] and self.C_SmallBody_queue[1] and self.C_DownTrend and self.C_BlackBody_queue[2] and self.C_BodyHi_queue[1] < self.C_BodyLo_queue[2] and self.C_BlackBody_queue[1] and C_WhiteBody and C_BodyHi <= self.C_BodyLo_queue[2] and C_BodyHi >= self.C_BodyHi_queue[1]:
                                            self.C_DownsideTasukiGapBearish = True
                                        if self.C_DownsideTasukiGapBearish and self.DownSideTasukiGapInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):
                                            ttBearishDownsideTasukiGap = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishDownsideTasukiGap_list.append(ttBearishDownsideTasukiGap)
                                            self.current_candle.append("ttBearishDownsideTasukiGap")
                                        C_UpsideTasukiGapBullishNumberOfCandles = 3
                                        self.C_UpsideTasukiGapBullish = False
                                        #####
                                        if self.C_LongBody_queue[2] and self.C_SmallBody_queue[1] and self.C_UpTrend and self.C_WhiteBody_queue[2] and self. C_BodyLo_queue[1] > self.C_BodyHi_queue[2] and self.C_WhiteBody_queue[1] and C_BlackBody and C_BodyLo >= self.C_BodyHi_queue[2] and C_BodyLo <= self.C_BodyLo_queue[1]:
                                            self.C_UpsideTasukiGapBullish = True
                                        if self.C_UpsideTasukiGapBullish and self.UpsideTasukiGapInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):
                                            ttBullishUpsideTasukiGap = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBullishUpsideTasukiGap_list.append(ttBullishUpsideTasukiGap)
                                            self.current_candle.append("ttBullishUpsideTasukiGap")
                                        C_EveningDojiStarBearishNumberOfCandles = 3
                                        self.C_EveningDojiStarBearish = False
                                        if self.C_LongBody_queue[2] and self.C_IsDojiBody_queue[1] and C_LongBody and self.C_UpTrend and self.C_WhiteBody_queue[2] and self.C_BodyLo_queue[1] > self.C_BodyHi_queue[2] and C_BlackBody and C_BodyLo <= self.C_BodyMiddle_queue[2] and C_BodyLo > self.C_BodyLo_queue[2] and self.C_BodyLo_queue[1] > C_BodyHi:
                                            self.C_EveningDojiStarBearish = True
                                        if self.C_EveningDojiStarBearish and self.EveningDojiStarInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):


                                            ttBearishEveningDojiStar = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishEveningDojiStar_list.append(ttBearishEveningDojiStar)
                                            self.current_candle.append("ttBearishEveningDojiStar")
                                        C_DojiStarBearishNumberOfCandles = 2
                                        self.C_DojiStarBearish = False
                                        if self.C_UpTrend and self.C_WhiteBody_queue[1] and self.C_LongBody_queue[1] and C_IsDojiBody and C_BodyLo > self.C_BodyHi_queue[1]:
                                            self.C_DojiStarBearish = True
                                        if self.C_DojiStarBearish and self.DojiStarInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):

                                            ttBearishDojiStar = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishDojiStar_list = ttBearishDojiStar
                                            self.current_candle.append("ttBearishDojiStar")
                                        C_DojiStarBullishNumberOfCandles = 2
                                        self.C_DojiStarBullish = False
                                        if self.C_DownTrend and self.C_BlackBody_queue[1] and self.C_LongBody_queue[1] and C_IsDojiBody and C_BodyHi < self.C_BodyLo_queue[1]:
                                            self.C_DojiStarBullish = True
                                        if self.C_DojiStarBullish and self.DojiStarInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):


                                            ttBullishDojiStar = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                            self.ttBullishDojiStar_list.append(ttBullishDojiStar)
                                            self.current_candle.append("ttBullishDojiStar")
                                        C_MorningDojiStarBullishNumberOfCandles = 3
                                        self.C_MorningDojiStarBullish = False
                                        if self.C_LongBody_queue[2] and self.C_IsDojiBody_queue[1] and C_LongBody and self.C_DownTrend and self.C_BlackBody_queue[2] and self.C_BodyHi_queue[1] < self.C_BodyLo_queue[2] and C_WhiteBody and C_BodyHi >= self.C_BodyMiddle_queue[2] and C_BodyHi < self.C_BodyHi_queue[2] and self.C_BodyHi_queue[1] < C_BodyLo:
                                            self.C_MorningDojiStarBullish = True
                                        if self.C_MorningDojiStarBullish and self.MorningDojiStarInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):
                                            ttBullishMorningDojiStar = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                            self.ttBullishMorningDojiStar_list.append(ttBullishMorningDojiStar)
                                            self.current_candle.append("ttBullishMorningDojiStar")
                                        C_PiercingBullishNumberOfCandles = 2
                                        self.C_PiercingBullish = False
                                        if (self.C_DownTrend_queue[1] and self.C_BlackBody_queue[1] and self.C_LongBody_queue[1]) and (C_WhiteBody and open <= self.low_queue[1] and close > self.C_BodyMiddle_queue[1] and close < self.open_queue[1]):
                                            self.C_PiercingBullish = True
                                        if self.C_PiercingBullish and self.PiercingInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):


                                            ttBullishPiercing = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                            self.ttBullishPiercing_list.append(ttBullishPiercing)
                                            self.current_candle.append("ttBullishPiercing")
                                        C_HammerBullishNumberOfCandles = 1
                                        self.C_HammerBullish = False
                                        if C_SmallBody and C_Body > 0 and C_BodyLo > hl2 and C_DnShadow >= self.C_Factor * C_Body and not C_HasUpShadow:
                                            if self.C_DownTrend:
                                                self.C_HammerBullish = True
                                        if self.C_HammerBullish and self.HammerInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):


                                            ttBullishHammer = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                            self.ttBullishHammer_list.append(ttBullishHammer)
                                            self.current_candle.append("ttBullishHammer")
                                        C_HangingManBearishNumberOfCandles = 1
                                        self.C_HangingManBearish = False
                                        if C_SmallBody and C_Body > 0 and C_BodyLo > hl2 and C_DnShadow >= self.C_Factor * C_Body and not C_HasUpShadow:
                                            if self.C_UpTrend:
                                                self.C_HangingManBearish = True
                                        if self.C_HangingManBearish and self.HangingManInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):


                                            ttBearishHangingMan = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishHangingMan_list.append(ttBearishHangingMan)
                                            self.current_candle.append("ttBearishHangingMan")
                                        C_ShootingStarBearishNumberOfCandles = 1
                                        self.C_ShootingStarBearish = False
                                        if C_SmallBody and C_Body > 0 and C_BodyHi < hl2 and C_UpShadow >= self.C_Factor * C_Body and not C_HasDnShadow:
                                            if self.C_UpTrend:
                                                self.C_ShootingStarBearish = True
                                        if self.C_ShootingStarBearish and self.ShootingStarInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):


                                            ttBearishShootingStar = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishShootingStar_list.append(ttBearishShootingStar)
                                            self.current_candle.append("ttBearishShootingStar")
                                        C_InvertedHammerBullishNumberOfCandles = 1
                                        self.C_InvertedHammerBullish = False
                                        if C_SmallBody and C_Body > 0 and C_BodyHi < hl2 and C_UpShadow >= self.C_Factor * C_Body and not C_HasDnShadow:
                                            if self.C_DownTrend:
                                                self.C_InvertedHammerBullish = True
                                        if self.C_InvertedHammerBullish and self.InvertedHammerInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):


                                            ttBullishInvertedHammer = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                            self.ttBullishInvertedHammer_list.append(ttBullishInvertedHammer)
                                            self.current_candle.append("ttBullishInvertedHammer")
                                        C_MorningStarBullishNumberOfCandles = 3
                                        self.C_MorningStarBullish = False
                                        if self.C_LongBody_queue[2] and self.C_SmallBody_queue[1] and C_LongBody:
                                            if self.C_DownTrend and self.C_BlackBody_queue[2] and self.C_BodyHi_queue[1] < self.C_BodyLo_queue[2] and C_WhiteBody and C_BodyHi >= self.C_BodyMiddle_queue[2] and C_BodyHi < self.C_BodyHi_queue[2] and self.C_BodyHi_queue[1] < C_BodyLo:
                                                self.C_MorningStarBullish = True

                                        if self.C_MorningStarBullish and self.MorningStarInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):


                                            ttBullishMorningStar = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                            self.ttBullishMorningStar_list.append(ttBullishMorningStar)
                                            self.current_candle.append("ttBullishMorningStar")
                                        C_EveningStarBearishNumberOfCandles = 3
                                        self.C_EveningStarBearish = False
                                        if self.C_LongBody_queue[2] and self.C_SmallBody_queue[1] and C_LongBody:
                                            if self.C_UpTrend and self.C_WhiteBody_queue[2] and self.C_BodyLo_queue[1] > self.C_BodyHi_queue[2] and C_BlackBody and C_BodyLo <= self.C_BodyMiddle_queue[2] and C_BodyLo > self.C_BodyLo_queue[2] and self.C_BodyLo_queue[1] > C_BodyHi:
                                                self.C_EveningStarBearish = True
                                        if self.C_EveningStarBearish and self.EveningStarInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):


                                            ttBearishEveningStar = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishEveningStar_list.append(ttBearishEveningStar)
                                            self.current_candle.append("ttBearishEveningStar")
                                        C_MarubozuWhiteBullishNumberOfCandles = 1
                                        C_MarubozuShadowPercentWhite = 5.0
                                        self.C_MarubozuWhiteBullish = C_WhiteBody and C_LongBody and C_UpShadow <= C_MarubozuShadowPercentWhite / 100 * C_Body and C_DnShadow <= C_MarubozuShadowPercentWhite / 100 * C_Body and C_WhiteBody
                                        if self.C_MarubozuWhiteBullish and self.MarubozuWhiteInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):


                                            ttBullishMarubozuWhite = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                            self.ttBullishMarubozuWhite_list.append(ttBullishMarubozuWhite)
                                            self.current_candle.append("ttBullishMarubozuWhite")
                                        C_MarubozuBlackBearishNumberOfCandles = 1
                                        C_MarubozuShadowPercentBearish = 5.0
                                        self.C_MarubozuBlackBearish = C_BlackBody and C_LongBody and C_UpShadow <= C_MarubozuShadowPercentBearish / 100 * C_Body and C_DnShadow <= C_MarubozuShadowPercentBearish / 100 * C_Body and C_BlackBody
                                        if self.C_MarubozuBlackBearish and self.MarubozuBlackInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):


                                            ttBearishMarubozuBlack = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishMarubozuBlack_list.append(ttBearishMarubozuBlack)
                                            self.current_candle.append("ttBearishMarubozuBlack")
                                        C_DojiNumberOfCandles = 1
                                        self.C_DragonflyDoji = C_IsDojiBody and C_UpShadow <= C_Body
                                        self.C_GravestoneDojiOne = C_IsDojiBody and C_DnShadow <= C_Body
                                        if C_Doji and not self.C_DragonflyDoji and not self.C_GravestoneDojiOne and self.DojiInput:


                                            ttDoji = (self.bar_index, patternLabelPosLow, self.label_color_neutral)
                                            self.ttDoji_list.append(ttDoji)
                                            self.current_candle.append("ttDoji")
                                        C_GravestoneDojiBearishNumberOfCandles = 1
                                        self.C_GravestoneDojiBearish = C_IsDojiBody and C_DnShadow <= C_Body
                                        if self.C_GravestoneDojiBearish and self.GravestoneDojiInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):


                                            ttBearishGravestoneDoji = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishGravestoneDoji_list.append(ttBearishGravestoneDoji)
                                        C_DragonflyDojiBullishNumberOfCandles = 1
                                        self.C_DragonflyDojiBullish = C_IsDojiBody and C_UpShadow <= C_Body
                                        if self.C_DragonflyDojiBullish and self.DragonflyDojiInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):


                                            ttBullishDragonflyDoji = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                            self.ttBullishDragonflyDoji_list.append(ttBullishDragonflyDoji)
                                            self.current_candle.append("ttBullishDragonflyDoji")
                                        C_HaramiCrossBullishNumberOfCandles = 2
                                        self.C_HaramiCrossBullish = self.C_LongBody_queue[1] and self.C_BlackBody_queue[1] and self.C_DownTrend_queue[1] and C_IsDojiBody and high <= self.C_BodyHi_queue[1] and low >= self.C_BodyLo_queue[1]
                                        if self.C_HaramiCrossBullish and self.HaramiCrossInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):

                                            ttBullishHaramiCross = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                            self.ttBullishHaramiCross_list.append(ttBullishHaramiCross)
                                            self.current_candle.append("ttBullishHaramiCross")
                                        C_HaramiCrossBearishNumberOfCandles = 2
                                        self.C_HaramiCrossBearish = self.C_LongBody_queue[1] and self.C_WhiteBody_queue[1] and self.C_UpTrend_queue[1] and C_IsDojiBody and high <= self.C_BodyHi_queue[1] and low >= self.C_BodyLo_queue[1]
                                        if self.C_HaramiCrossBearish and self.HaramiCrossInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):


                                            ttBearishHaramiCross = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishHaramiCross_list.append(ttBearishHaramiCross)
                                            self.current_candle.append("ttBearishHaramiCross")
                                        C_HaramiBullishNumberOfCandles = 2
                                        self.C_HaramiBullish = self.C_LongBody_queue[1] and self.C_BlackBody_queue[1] and self.C_DownTrend_queue[1] and C_WhiteBody and C_SmallBody and high <= self.C_BodyHi_queue[1] and low >= self.C_BodyLo_queue[1]
                                        if self.C_HaramiBullish and self.HaramiInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):


                                            ttBullishHarami = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                            self.ttBullishHarami_list.append(ttBullishHarami)
                                            self.current_candle.append("ttBullishHarami")
                                        C_HaramiBearishNumberOfCandles = 2
                                        self.C_HaramiBearish = self.C_LongBody_queue[1] and self.C_WhiteBody_queue[1] and self.C_UpTrend_queue[1] and C_BlackBody and C_SmallBody and high <= self.C_BodyHi_queue[1] and low >= self.C_BodyLo_queue[1]
                                        if self.C_HaramiBearish and self.HaramiInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):


                                            ttBearishHarami = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishHarami_list.append(ttBearishHarami)
                                            self.current_candle.append("ttBearishHarami")
                                        C_LongLowerShadowBullishNumberOfCandles = 1
                                        C_LongLowerShadowPercent = 75.0
                                        self.C_LongLowerShadowBullish = C_DnShadow > C_Range / 100 * C_LongLowerShadowPercent
                                        if self.C_LongLowerShadowBullish and self.LongLowerShadowInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):

                                            ttBullishLongLowerShadow = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                            self.ttBullishLongLowerShadow_list.append(ttBullishLongLowerShadow)
                                            self.current_candle.append("ttBullishLongLowerShadow")
                                        C_LongUpperShadowBearishNumberOfCandles = 1
                                        C_LongShadowPercent = 75.0
                                        self.C_LongUpperShadowBearish = C_UpShadow > C_Range / 100 * C_LongShadowPercent
                                        if self.C_LongUpperShadowBearish and self.LongUpperShadowInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):


                                            ttBearishLongUpperShadow = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishLongUpperShadow_list.append(ttBearishLongUpperShadow)
                                            self.current_candle.append("ttBearishLongUpperShadow")
                                        C_SpinningTopWhiteNumberOfCandles = 1
                                        C_SpinningTopWhitePercent = 34.0
                                        self.C_IsSpinningTopWhite = C_DnShadow >= C_Range / 100 * C_SpinningTopWhitePercent and C_UpShadow >= C_Range / 100 * C_SpinningTopWhitePercent and not C_IsDojiBody
                                        self.C_SpinningTopWhite = self.C_IsSpinningTopWhite and C_WhiteBody
                                        if self.C_SpinningTopWhite and self.SpinningTopWhiteInput:

                                            ttSpinningTopWhite = (self.bar_index, patternLabelPosLow, self.label_color_neutral)
                                            self.ttSpinningTopWhite_list.append(ttSpinningTopWhite)
                                            self.current_candle.append("ttSpinningTopWhite")
                                        C_SpinningTopBlackNumberOfCandles = 1
                                        C_SpinningTopBlackPercent = 34.0
                                        self.C_IsSpinningTop = C_DnShadow >= C_Range / 100 * C_SpinningTopBlackPercent and C_UpShadow >= C_Range / 100 * C_SpinningTopBlackPercent and not C_IsDojiBody
                                        self.C_SpinningTopBlack = self.C_IsSpinningTop and C_BlackBody
                                        if self.C_SpinningTopBlack and self.SpinningTopBlackInput:

                                            ttSpinningTopBlack = (self.bar_index, patternLabelPosLow, self.label_color_neutral)
                                            self.ttSpinningTopBlack_list.append(ttSpinningTopBlack)
                                            self.current_candle.append("ttSpinningTopBlack")
                                        C_ThreeWhiteSoldiersBullishNumberOfCandles = 3
                                        C_3WSld_ShadowPercent = 5.0
                                        C_3WSld_HaveNotUpShadow = C_Range * C_3WSld_ShadowPercent / 100 > C_UpShadow
                                        self.C_3WSld_HaveNotUpShadow_queue.appendleft(C_3WSld_HaveNotUpShadow)
                                        if len(self.C_3WSld_HaveNotUpShadow_queue) == 5:
                                            self.C_ThreeWhiteSoldiersBullish = False
                                            if C_LongBody and self.C_LongBody_queue[1] and self.C_LongBody_queue[2]:
                                                if C_WhiteBody and self.C_WhiteBody_queue[1] and self.C_WhiteBody_queue[2]:
                                                    self.C_ThreeWhiteSoldiersBullish = close > self.close_queue[1] and self.close_queue[1] > self.close_queue[2] and open < self.close_queue[1] and open > self.open_queue[1] and self.open_queue[1] < self.close_queue[2] and self.open_queue[1] > self.open_queue[2] and C_3WSld_HaveNotUpShadow and self.C_3WSld_HaveNotUpShadow_queue[1] and self.C_3WSld_HaveNotUpShadow_queue[2]
                                            if self.C_ThreeWhiteSoldiersBullish and self.ThreeWhiteSoldiersInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):


                                                ttBullishThreeWhiteSoldiers = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                                self.ttBullishThreeWhiteSoldiers_list.append(ttBullishThreeWhiteSoldiers)
                                                self.current_candle.append("ttBullishThreeWhiteSoldiers")
                                        C_ThreeBlackCrowsBearishNumberOfCandles = 3
                                        C_3BCrw_ShadowPercent = 5.0
                                        C_3BCrw_HaveNotDnShadow = C_Range * C_3BCrw_ShadowPercent / 100 > C_DnShadow
                                        self.C_3BCrw_HaveNotDnShadow_queue.appendleft(C_3BCrw_HaveNotDnShadow)
                                        self.C_ThreeBlackCrowsBearish = False
                                        if len(self.C_3BCrw_HaveNotDnShadow_queue) == 5:
                                            if C_LongBody and self.C_LongBody_queue[1] and self.C_LongBody_queue[2]:
                                                if C_BlackBody and self.C_BlackBody_queue[1] and self.C_BlackBody_queue[2]:
                                                    self.C_ThreeBlackCrowsBearish = close < self.close_queue[1] and self.close_queue[1] < self.close_queue[2] and open > self.close_queue[1] and open < self.open_queue[1] and self.open_queue[1] > self.close_queue[2] and self.open_queue[1] < self.open_queue[2] and C_3BCrw_HaveNotDnShadow and self.C_3BCrw_HaveNotDnShadow_queue[1] and self.C_3BCrw_HaveNotDnShadow_queue[2]
                                            if self.C_ThreeBlackCrowsBearish and self.ThreeBlackCrowsInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):


                                                ttBearishThreeBlackCrows = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                                self.ttBearishThreeBlackCrows_list.append(ttBearishThreeBlackCrows)
                                                self.current_candle.append("ttBearishThreeBlackCrows")
                                        C_EngulfingBullishNumberOfCandles = 2
                                        self.C_EngulfingBullish = self.C_DownTrend and C_WhiteBody and C_LongBody and self.C_BlackBody_queue[1] and self.C_SmallBody_queue[1] and close >= self.open_queue[1] and open <= self.close_queue[1] and (close > self.open_queue[1] or open < self.close_queue[1])

                                        if self.C_EngulfingBullish and self.EngulfingInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):


                                            ttBullishEngulfing = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                            self.ttBullishEngulfing_list.append(ttBullishEngulfing)
                                            self.current_candle.append("ttBullishEngulfing")
                                        C_EngulfingBearishNumberOfCandles = 2
                                        self.C_EngulfingBearish = self.C_UpTrend and C_BlackBody and C_LongBody and self.C_WhiteBody_queue[1] and self.C_SmallBody_queue[1] and close <= self.open_queue[1] and open >= self.close_queue[1] and (close < self.open_queue[1] or open > self.close_queue[1])
                                        if self.C_EngulfingBearish and self.EngulfingInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):


                                            ttBearishEngulfing = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                            self.ttBearishEngulfing_list.append(ttBearishEngulfing)
                                            self.current_candle.append("ttBearishEngulfing")
                                        C_AbandonedBabyBullishNumberOfCandles = 3
                                        self.C_AbandonedBabyBullish = self.C_DownTrend_queue[2] and self.C_BlackBody_queue[2] and self.C_IsDojiBody_queue[1] and self.low_queue[2] > self.high_queue[1] and C_WhiteBody and self.high_queue[1] < low
                                        if self.C_AbandonedBabyBullish and self.AbandonedBabyInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):


                                            ttBullishAbandonedBaby = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                            self.ttBullishAbandonedBaby_list.append(ttBullishAbandonedBaby)
                                            self.current_candle.append("ttBullishAbandonedBaby")
                                        C_AbandonedBabyBearishNumberOfCandles = 3
                                        self.C_AbandonedBabyBearish = self.C_UpTrend_queue[2] and self.C_WhiteBody_queue[2] and self.C_IsDojiBody_queue[1] and self.high_queue[2] < self.low_queue[1] and C_BlackBody and self.low_queue[1] > high
                                        if self.C_AbandonedBabyBearish and self.AbandonedBabyInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):


                                            ttBearishAbandonedBaby = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)

                                            self.ttBearishAbandonedBaby_list.append(ttBearishAbandonedBaby)
                                            self.current_candle.append("ttBearishAbandonedBaby")
                                        C_TriStarBullishNumberOfCandles = 3
                                        C_3DojisBullish = self.C_Doji_queue[2] and self.C_Doji_queue[1] and C_Doji
                                        C_BodyGapUpBullish = self.C_BodyHi_queue[1] < C_BodyLo
                                        C_BodyGapDnBullish = self.C_BodyLo_queue[1] > C_BodyHi
                                        self.C_BodyGapUpBullish_queue.appendleft(C_BodyGapUpBullish)
                                        self.C_BodyGapDnBullish_queue.appendleft(C_BodyGapDnBullish)
                                        if len(self.C_BodyGapUpBullish_queue) == 5:
                                            self.C_TriStarBullish = C_3DojisBullish and self.C_DownTrend_queue[2] and self.C_BodyGapDnBullish_queue[1] and C_BodyGapUpBullish
                                            if self.C_TriStarBullish and self.TriStarInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):


                                                ttBullishTriStar = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                                self.ttBullishTriStar_list.append(ttBullishTriStar)
                                                self.current_candle.append("ttBullishTriStar")
                                        C_TriStarBearishNumberOfCandles = 3
                                        C_3Dojis = self.C_Doji_queue[2] and self.C_Doji_queue[1] and C_Doji
                                        C_BodyGapUp = self.C_BodyHi_queue[1] < C_BodyLo
                                        C_BodyGapDn = self.C_BodyLo_queue[1] > C_BodyHi
                                        self.C_BodyGapUp_queue.appendleft(C_BodyGapUp)
                                        self.C_BodyGapDn_queue.appendleft(C_BodyGapDn)
                                        if len(self.C_BodyGapUp_queue) == 5:
                                            self.C_TriStarBearish = C_3Dojis and self.C_UpTrend_queue[2] and self.C_BodyGapUp_queue[1] and C_BodyGapDn
                                            if self.C_TriStarBearish and self.TriStarInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):


                                                ttBearishTriStar = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                                self.ttBearishTriStar_list.append(ttBearishTriStar)
                                                self.current_candle.append("ttBearishTriStar")
                                        C_KickingBullishNumberOfCandles = 2
                                        C_MarubozuShadowPercent = 5.0
                                        C_Marubozu = C_LongBody and C_UpShadow <= C_MarubozuShadowPercent / 100 * C_Body and C_DnShadow <= C_MarubozuShadowPercent / 100 * C_Body
                                        C_MarubozuWhiteBullishKicking = C_Marubozu and C_WhiteBody
                                        C_MarubozuBlackBullish = C_Marubozu and C_BlackBody
                                        self.C_MarubozuBlackBullish_queue.appendleft(C_MarubozuBlackBullish)
                                        self.C_MarubozuWhiteBullishKicking_queue.appendleft(C_MarubozuWhiteBullishKicking)
                                        if len(self.C_MarubozuWhiteBearish_queue) == 5:
                                            self.C_KickingBullish = self.C_MarubozuBlackBullish_queue[1] and C_MarubozuWhiteBullishKicking and self.high_queue[1] < low
                                            if self.C_KickingBullish and self.KickingInput and (self.CandleType == "BULLISH" or self.CandleType =="BOTH"):


                                                ttBullishKicking = (self.bar_index, patternLabelPosLow, self.label_color_bullish)
                                                self.ttBullishKicking_list.append(ttBullishKicking)
                                                self.current_candle.append("ttBullishKicking")
                                        C_KickingBearishNumberOfCandles = 2
                                        C_MarubozuBullishShadowPercent = 5.0
                                        C_MarubozuBearishKicking = C_LongBody and C_UpShadow <= C_MarubozuBullishShadowPercent / 100 * C_Body and C_DnShadow <= C_MarubozuBullishShadowPercent / 100 * C_Body
                                        C_MarubozuWhiteBearish = C_MarubozuBearishKicking and C_WhiteBody
                                        C_MarubozuBlackBearishKicking = C_MarubozuBearishKicking and C_BlackBody
                                        self.C_MarubozuWhiteBearish_queue.appendleft(C_MarubozuWhiteBearish)
                                        if len(self.C_MarubozuWhiteBearish_queue) == 5:
                                            self.C_KickingBearish = self.C_MarubozuWhiteBearish_queue[1] and C_MarubozuBlackBearishKicking and self.low_queue[1] > high
                                            if self.C_KickingBearish and self.KickingInput and (self.CandleType == "BEARISH" or self.CandleType == "BOTH"):


                                                ttBearishKicking = (self.bar_index, patternLabelPosHigh, self.label_color_bearish)
                                                self.ttBearishKicking_list.append(ttBearishKicking)
                                                self.current_candle.append("ttBearishKicking")


                                                ttAllCandlestickPatterns = (self.bar_index, patternLabelPosLow, self.label_color_neutral)
                                                self.ttAllCandlestickPatterns_list.append(ttAllCandlestickPatterns)


                                self.check_conditions()



    def reset_patterns(self):
        self.current_candle = []

    def check_conditions(self):
        long_conditions = []
        short_conditions = []



    def calculate_true_range(self, high, low, close):
        high_minus_low = high - low
        high_minus_close = abs(high - close[1])
        low_minus_close = abs(low - close[1])
        true_range = max(high_minus_low, high_minus_close, low_minus_close)
        return true_range

    def calculate_sma(self, list_item):
        current_value = sum(list_item) / len(list_item)
        return current_value


    def calculate_ema(self, list_item, current_value):
        if current_value is None:
            current_value = sum(list_item) / len(list_item)
            return current_value
        else:
            k = 2 / (len(list_item) + 1)
            current_value = list_item[0] * k + current_value * (1 - k)
            return current_value