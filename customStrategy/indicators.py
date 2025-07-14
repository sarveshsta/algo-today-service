# import pandas_ta as ta

# def apply_indicator(df, indicator: str, length: int = 14):
#     """
#     Applies the specified indicator to the DataFrame and returns the modified DataFrame.
#     Supports RSI, EMA, SMA, MACD, etc.
#     """
#     indicator = indicator.lower()

#     try:
#         if indicator == "rsi":
#             df["rsi"] = ta.rsi(df["close"], length=length)
#         elif indicator == "ema":
#             df["ema"] = ta.ema(df["close"], length=length)
#         elif indicator == "sma":
#             df["sma"] = ta.sma(df["close"], length=length)
#         elif indicator == "macd":
#             macd = ta.macd(df["close"])
#             df["macd"] = macd["MACD_12_26_9"]
#             df["macd_signal"] = macd["MACDs_12_26_9"]
#             df["macd_hist"] = macd["MACDh_12_26_9"]
#         else:
#             raise ValueError(f"Indicator '{indicator}' not supported")

#         return df

#     except Exception as e:
#         print(f"❌ Failed to apply indicator '{indicator}': {e}")
#         return df
import pandas_ta as ta

def apply_indicator(df, indicator: str, length: int = 14):
    """
    Applies the specified indicator to the DataFrame and returns the modified DataFrame.
    Supports RSI, EMA, SMA, MACD, etc.
    """
    indicator = indicator.lower()

    try:
        if indicator == "rsi":
            df["rsi"] = ta.rsi(df["close"], length=length)
        elif indicator == "ema":
            df["ema"] = ta.ema(df["close"], length=length)
        elif indicator == "sma":
            df["sma"] = ta.sma(df["close"], length=length)
        elif indicator == "macd":
            macd = ta.macd(df["close"])
            if macd is not None and not macd.empty:
                df["macd"] = macd.iloc[:, 0]  # MACD line
                df["macd_signal"] = macd.iloc[:, 1]  # Signal line
                df["macd_hist"] = macd.iloc[:, 2]  # Histogram
            else:
                raise ValueError("MACD output is empty or None")
        else:
            raise ValueError(f"Indicator '{indicator}' not supported")

        return df

    except Exception as e:
        print(f"❌ Failed to apply indicator '{indicator}': {e}")
        return df
