from dotenv import load_dotenv


load_dotenv()
# api_key = os.getenv("API_KEY")
# client_code = os.getenv("CLIENT_CODE")
# password = os.getenv("PASSWORD")
# token_code = os.getenv("TOKEN_CODE")

api_key = "T4MHVpXH"
client_code = "J263557"
password = "7753"
token_code = "3MYXRWJIJ2CZT6Y5PD2EU5RNNQ"

# constant data
global_order_id = 1111

# index details
NFO_DATA_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
OPT_TYPE = "OPTIDX"
EXCH_TYPE = "NFO"

# client code to get LTP data
LTP_API_KEY = "MolOSZTR"
LTP_CLIENT_CODE = "S55329579"
LTP_PASSWORD = "4242"
LTP_TOKEN_CODE = "QRLYAZPZ6LMTH5AYILGTWWN26E"

# price comparision
OHLC_1 = "Close"
OHLC_2 = "High"
index_candle_data = []

# buying condition comparision
buying_multiplier = 1.01
buying_OHLC = "High"

# selling condition comparision
trail_ltp_multiplier = 1.12
price_vs_ltp_mulitplier = 0.95

# stop loss condition
selling_OHLC1 = "High"
selling_OHLC1_multiplier = 1.10

selling_OHLC2 = "Low"
selling_OHLC2_multiplier = 0.95
# variables initialisation complete