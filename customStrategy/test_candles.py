# test_candles.py
from utils import get_candle_data

# Replace this with your actual token/symbol
symbol = ["NIFTY26JUN2523000CE"]

df = get_candle_data(token=symbol, exchange="NFO", interval="ONE_MINUTE", days=1)

if df.empty:
    print("❌ No candle data returned.")
else:
    print("✅ Candle data fetched successfully:")
    print(df.tail())
