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
#             if macd is not None and not macd.empty:
#                 df["macd"] = macd.iloc[:, 0]  # MACD line
#                 df["macd_signal"] = macd.iloc[:, 1]  # Signal line
#                 df["macd_hist"] = macd.iloc[:, 2]  # Histogram
#             else:
#                 raise ValueError("MACD output is empty or None")
#         else:
#             raise ValueError(f"Indicator '{indicator}' not supported")

#         return df

#     except Exception as e:
#         print(f"❌ Failed to apply indicator '{indicator}': {e}")
#         return df


import pandas_ta as ta
import numpy as np

def apply_indicator(df, indicator: str, length: int = 14):
    """
    Applies the specified indicator to the DataFrame and returns the modified DataFrame.
    Supports RSI, EMA, SMA, MACD, etc.
    """
    indicator = indicator.lower()

    try:
        if indicator == "rsi":
            # Calculate RSI with validation
            rsi_values = ta.rsi(df["close"], length=length)
            
            # Validate RSI values are within proper bounds (0-100)
            if rsi_values is not None:
                # Check for invalid values
                invalid_mask = (rsi_values < 0) | (rsi_values > 100) | np.isnan(rsi_values)
                
                if invalid_mask.any():
                    print(f"⚠️  Warning: Found {invalid_mask.sum()} invalid RSI values. Clipping to 0-100 range.")
                    # Clip values to valid range
                    rsi_values = np.clip(rsi_values, 0, 100)
                
                df["rsi"] = rsi_values
                
                # Additional validation check
                print(f"✅ RSI applied successfully. Range: {df['rsi'].min():.2f} - {df['rsi'].max():.2f}")
            else:
                raise ValueError("RSI calculation returned None")
                
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