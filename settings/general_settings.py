import os
#from dotenv import load_dotenv
#load_dotenv()
from decouple import config


##################################################################  BACKTEST SETTINGS  ########################################################################

# Dates need to be in this format
# '2023-01-01'
# Earliest Date available is september 2017
START_DATE = '2023-01-01'
END_DATE = '2023-01-31'

STRATEGY_PARAMETER_MODE = "AUTO"
ENABLE_DEBUG_MODE = False


ENTRY_TIMEFRAME = "1m"
EXIT_TIMEFRAME = "1m"


LOAD_STRATEGY = False
# Strategy_name_from_DB
STRATEGY_TO_LOAD = "MFI_15MIN_TEST"

# IF THIS IS SET TO True THEN THE BOT WILL USE THE API CREDENTIALS OF THE REAL BINANCE ACCOUNT PROVIDED BY MAEN
ENABLE_LIVE_MODE = True

if not ENABLE_LIVE_MODE:
    API_KEY = config('API_KEY')
    API_SECRET = config('API_SECRET')
else:
    API_KEY = config('API_KEY_REAL')
    API_SECRET = config('API_SECRET_REAL')

TELEGRAM_ID = config('TELEGRAM_ID')
TELEGRAM_TOKEN = config('TELEGRAM_TOKEN')


SYMBOL = "BTCUSDT"

# Cash is in USDT
START_CASH = 150

FEE_RATE = 0.05


# Select quantity mode, can either select "PERCENTAGE" or "FIXED" here
QUANTITY_MODE = "PERCENTAGE"

# Trade Quantity as Percentage of START_CASH
QUANTITY_PERCENTAGE = 99

# Trade Quantity in USDT
QUANTITY = 5

RECORD_INDICATOR_VALUES = False

CALENDAR_API_KEY = config('CALENDAR_API_KEY')
CSV_FILE_PATH = str(os.environ.get('CSV_FILE_PATH'))
PRICE_DATABASE_PATH = str(os.environ.get('PRICE_DATABASE_PATH'))
BACKTEST_DATABASE_PATH = str(os.environ.get('BACKTEST_DATABASE_PATH'))


AVOID_DUPLICATE = 177

##################################################################  ACCOUNT SETTINGS  ########################################################################

# Pick between "USDS_M_FUTURES" and "SPOT"
TRADING_MODE = "USDS_M_FUTURES"


# Pick between "ISOLATED" and "CROSSED"
MARGIN_TYPE = "ISOLATED"

# Pick a number between 1 and 125
LEVERAGE = 1

# Pick between "HEDGE_MODE" and "ONE_WAY_MODE"
# Highly recommended to leave it as "HEDGE_MODE"
POSITION_MODE = "ONE_WAY_MODE"





##################################################################  EVENT SETTINGS  ########################################################################


USE_CALENDAR = False

# 1 = Low
# 2 = Medium
# 3 = High
MINIMUM_EVENT_IMPACT = 1


USE_DISABLE_BEFORE_EVENT = False
USE_DISABLE_AFTER_EVENT = True

DISABLE_X_MINUTES_BEFORE_EVENT = 60
DISABLE_X_MINUTES_AFTER_EVENT = 60



##################################################################  ORDER SETTINGS  ########################################################################

# Pick between "MARKET", "LIMIT", "MAKER"
# Maker currently not available
ORDER_MODE = "MARKET"

# Pick between "MARKET_LEVEL" and "BOT_LEVEL"
STOP_LOSS_MODE = "MARKET_LEVEL"

# Limit order entry settings
# "PERCENTAGE" or "QUOTE_CURRENCY"
LIMIT_ORDER_AMOUNT_TYPE = "QUOTE_CURRENCY"
# PLEASE MAKE SURE THAT THIS IS LESS THAN THE ENTRY TIMEFRAME
# TIME LIMIT IS IN SECONDS
TIME_LIMIT = 30
SLIPPAGE_LIMIT = 100
TRAILING_MAX_OFFSET = 30
TRAILING_MIN_OFFSET = 10
SLIPPAGE_LIMIT_PERCENTAGE = 0.05
TRAILING_MAX_OFFSET_PERCENTAGE = 0.03
TRAILING_MIN_OFFSET_PERCENTAGE = 0.01

MAX_RETRIES = 5
RETRY_DELAY = 2
PERCENTAGE_INCREMENT = 0.1
ORDER_TIMEOUT = 30




##################################################################  GENERAL SETTINGS  ########################################################################

# Inputs below are all either True or False
ENABLE_LONGS = True
ENABLE_SHORTS = True
ENABLE_BASELINE = True

ENABLE_CONDITION_1 = True
ENABLE_CONDITION_2 = True
ENABLE_CONDITION_3 = True
ENABLE_CONDITION_4 = False
ENABLE_CONDITION_5 = False
ENABLE_CONDITION_6 = False
ENABLE_CONDITION_7 = False
ENABLE_CONDITION_8 = False


ENTRY_ON_CONDITION_TRIGGER = True



ENABLE_TREND = False
ENABLE_LOSS_OF_TREND_EXIT = False

ENABLE_ENTRY_FILTER = False

# ATR Multiplier
MAX_ATR_ON_ENTRY = 2

# ATR Multiplier
MIN_ATR_ON_ENTRY = 1


# "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"
WEEKDAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

# "LONDON", "NEW YORK", "ASIA" or "ALL"
SESSIONS = ["ALL"]



##################################################################  CONDITION MAPPING SETTINGS  ########################################################################

# Valid indicator options here are;
# "PMARP"
# "LRSI"
# "BBWP"
# "DMI"
# "WADDAH"
# "WAVE"
# "CORAL"
# "MFI"
# "AROON"

# NEEDS TO BE ALL CAPS and EXACT SPELLING HERE,
# Indicator settings and Buy/Sell conditions to be configured in the indicator_settings.py file
CONDITIONS = {
            "CONDITION_1": "PMARP",
            "CONDITION_2": "",
            "CONDITION_3": "",
            "CONDITION_4": "",
            "CONDITION_5": "",
            "CONDITION_6": "",
            "CONDITION_7": "",
            "CONDITION_8": ""
            }


CONDITION_AND_OR =  {
            "CONDITION_1": "AND",
            "CONDITION_2": "",
            "CONDITION_3": "",
            "CONDITION_4": "",
            "CONDITION_5": "",
            "CONDITION_6": "",
            "CONDITION_7": "",
            "CONDITION_8": ""
            }



##################################################################  BASELINE SETTINGS  ########################################################################


# Pick between "MCGINLEY DYNAMIC", "CORAL", "VIDYA", "JURIK", "KMA",  "SMA", "EMA", "VWMA"
BASELINE_TYPE = "CORAL"

# True or False
ENTRY_ON_CROSS = True
ENTRY_ON_RETEST = False

# "UNLIMITED" or Numerical Value
ENTRY_AFTER_BASELINE_CROSS = "UNLIMITED"

# Percentage 1 = 1%
RETEST_PROXIMITY = 0.1

# Available Timeframes are;
# "1m"
# "3m"
# "5m"
# "15m"
# "30m"
# "1h"
# "2h"
# "4h"
# "6h"
# "8h"
# "12h"
# "1d"
# "3d"
# "1w"
BASELINE_TIMEFRAME = "1m"

# If any of these indicators are used as baseline, then these settings will apply to the indicators, if available they can also simultaneously be used as a normal condition indicator,
# where in that case the settings of the indicator_settings.py file are used.
# Options should closely resemble their TradingView counter-parts.
BASELINE_MCG_SOURCE = "CLOSE"
BASLINE_MCG_PERIOD = 12
BASELINE_MCG_CONSTANT = 5
BASELINE_MCG_AVERAGE_MODE = "EMA"

BASELINE_CORAL_SMOOTHING_PERIOD = 7
BASELINE_CORAL_CONSTANT_D = 0.4
BASELINE_CORAL_RIBBON_MODE = False

BASELINE_VIDYA_PERIOD = 14
BASELINE_VIDAY_HISTORY_PERIOD = 14

BASELINE_JURIK_LENGTH = 14
BASELINE_JURIK_PHASE = 50
BASELINE_JURIK_POWER = 2
BASELINE_JURIK_SOURCE = "CLOSE"

BASELINE_KMA_LENGTH = 14





##################################################################  TREND SETTINGS  ########################################################################


# Available Timeframes are;
# "1m"
# "3m"
# "5m"
# "15m"
# "30m"
# "1h"
# "2h"
# "4h"
# "6h"
# "8h"
# "12h"
# "1d"
# "3d"
# "1w"
TREND_TIMEFRAME_FAST = "1m"
TREND_TIMEFRAME_SLOW = "1m"

# Pick between "SMA", "EMA", "VWMA", "SMMA", "DEMA", "KMA", "MCG", "JURIK"
TREND_TYPE_FAST = "VWMA"
TREND_TYPE_SLOW = "VWMA"

TREND_PERIOD_FAST = 5
TREND_PERIOD_SLOW = 21

PRICE_ABOVE_BELOW_TREND = True
PRICE_BELOW_SLOW = True
PRICE_BELOW_FAST = True
PRICE_ABOVE_FAST = True
PRICE_ABOVE_SLOW = True
# If any of these indicators are used as Trend indicators, then these settings will apply to the indicators, if available they can also simultaneously be used as a normal condition indicator,
# where in that case the settings of the indicator_settings.py file are used.
# Options should closely resemble their TradingView counter-parts.

# Available options for SOURCE are:
# "CLOSE"
# "OPEN"
# "HIGH"
# "LOW"
# "HL2"
# "HLC3"
# "OHCL4"
# "HLCC4"
TREND_MCG_SOURCE_FAST = "CLOSE"
TREND_MCG_CONSTANT_FAST = 5
TREND_MCG_AVERAGE_MODE_FAST = "EMA"

TREND_MCG_SOURCE_SLOW = "CLOSE"
TREND_MCG_CONSTANT_SLOW = 5
TREND_MCG_AVERAGE_MODE_SLOW = "EMA"


TREND_JURIK_PHASE_FAST = 50
TREND_JURIK_POWER_FAST = 2
TREND_JURIK_SOURCE_FAST = "CLOSE"

TREND_JURIK_PHASE_SLOW = 50
TREND_JURIK_POWER_SLOW = 2
TREND_JURIK_SOURCE_SLOW = "CLOSE"



##################################################################  TAKE PROFIT SETTINGS  ########################################################################



ENABLE_TAKE_PROFIT_1 = True
TAKE_PROFIT_1 = {
    'ENABLE_PARTIAL_TP_PERCENTAGE': False,
    'PARTIAL_TP_PERCENTAGE': 50,
    'ENABLE_PERCENTAGE_TP': False,
    'TAKE_PROFIT_PERCENTAGE': 0.5,
    'ENABLE_ATR_TP': True,
    'TP_ATR_MULTIPLIER': 1,
    'ENABLE_FIXED_REWARD_TP': False,
    'FIXED_REWARD_TP': 0,
    'USE_EXIT_INDICATOR': ['PMARP']
}

ENABLE_TAKE_PROFIT_2 = False
TAKE_PROFIT_2 = {
    'ENABLE_PARTIAL_TP_PERCENTAGE': True,
    'PARTIAL_TP_PERCENTAGE': 50,
    'ENABLE_PERCENTAGE_TP': False,
    'TAKE_PROFIT_PERCENTAGE': 5,
    'ENABLE_ATR_TP': True,
    'TP_ATR_MULTIPLIER': 2,
    'ENABLE_FIXED_REWARD_TP': False,
    'FIXED_REWARD_TP': 200,
    'USE_EXIT_INDICATOR': []
}

ENABLE_TAKE_PROFIT_3 = False
TAKE_PROFIT_3 = {
    'ENABLE_PARTIAL_TP_PERCENTAGE': True,
    'PARTIAL_TP_PERCENTAGE': 50,
    'ENABLE_PERCENTAGE_TP': True,
    'TAKE_PROFIT_PERCENTAGE': 5,
    'ENABLE_ATR_TP': False,
    'TP_ATR_MULTIPLIER': 2,
    'ENABLE_FIXED_REWARD_TP': True,
    'FIXED_REWARD_TP': 200,
    'USE_EXIT_INDICATOR': []
}
# Pick between;
# "ATR_TP"
# "PERCENTAGE_TP"
# "FIXED_REWARD_TP"
STOP_PRIORITY = "ATR_TP"
USE_REAL_TIME_EXIT_INDICATORS = True

##################################################################  STOP LOSS SETTINGS  ########################################################################


USE_WICK_OR_CLOSE = "CLOSE"


ENABLE_ATR_EXIT = False

ATR_EXIT_SETTINGS = {
    'MULTIPLIER': 1,
    'ENABLE_TRAILING_STOP': True
}


ENABLE_FIXED_PERCENTAGE_EXIT = True

FIXED_PERCENTAGE_EXIT_SETTINGS = {
    'VALUE': 1,
    'ENABLE_TRAILING_STOP': True
}



ENABLE_FIXED_RISK_EXIT = True

FIXED_RISK_EXIT_SETTINGS = {
    'VALUE': 2,
    'ENABLE_TRAILING_STOP': True
}


##################################################################  EXIT INDICATOR SETTINGS  ########################################################################

ATR_PROFIT_TIMEFRAME = "1m"
ATR_PROFIT_LENGTH = 3

ATR_STOP_TIMEFRAME = "1m"
ATR_STOP_LENGTH = 3




# Available Timeframes are;
# "1m"
# "3m"
# "5m"
# "15m"
# "30m"
# "1h"
# "2h"
# "4h"
# "6h"
# "8h"
# "12h"
# "1d"
# "3d"
# "1w"
EXIT_PMARP_TIMEFRAME = "1m"

EXIT_PMARP_PRICE_SOURCE = "CLOSE"
EXIT_PMARP_INDICATOR = "PRICE MOVING AVERAGE RATIO PERCENTILE"
EXIT_PMARP_SIGNAL_MA = True
EXIT_PMARP_MA_LENGTH = 20
EXIT_PMARP_SIGNAL_MA_LENGTH = 20
EXIT_PMARP_MA_TYPE = "VWMA"
EXIT_PMARP_LOOKBACK = 350


# Options for "below" and "above" are:
# None to disable it,
# or any numerical input

# Options for cross_above and cross_below are:
# None to disable that option,
# "SIGNAL_MA",
# or any numerical input
EXIT_PMARP_CONFIG = {
    "long": {
        "below": None,
        "above": None,
        "cross_above": 75,
        "cross_below": None,
    },
    "short": {
        "below": None,
        "above": None,
        "cross_above": None,
        "cross_below": 25,
    }
}




# Available Timeframes are;
# "1m"
# "3m"
# "5m"
# "15m"
# "30m"
# "1h"
# "2h"
# "4h"
# "6h"
# "8h"
# "12h"
# "1d"
# "3d"
# "1w"
EXIT_REX_TIMEFRAME = "1m"

EXIT_REX_MA_TYPE = "EMA"
EXIT_REX_SMOOTHING_LENGTH = 14
EXIT_REX_SIGNAL_MA_TYPE = "EMA"
EXIT_REX_SIGNAL_SMOOTHING_LENGTH = 14


# Here cross_above_signal_line and cross_below_signal_line are boolean
# oversold_level and over_bought_level can be any numerical input or None to disable the options
EXIT_REX_CONFIG = {
    "long": {
        "cross_above_signal_line": True,
        "cross_below_signal_line": True,
        "oversold_level": 30,
        "over_bought_level": 80
    },
    "short": {
            "cross_above_signal_line": True,
            "cross_below_signal_line": True,
            "oversold_level": 30,
            "over_bought_level": None
        }
}
