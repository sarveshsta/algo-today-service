# import pandas_ta as ta
# import numpy as np

# def apply_indicator(df, indicator: str, length: int = 14):
#     """
#     Applies the specified indicator to the DataFrame and returns the modified DataFrame.
#     Supports RSI, EMA, SMA, MACD, etc.
#     """
#     indicator = indicator.lower()

#     try:
#         if indicator == "rsi":
#             # Calculate RSI with validation
#             rsi_values = ta.rsi(df["close"], length=length)
            
#             # Validate RSI values are within proper bounds (0-100)
#             if rsi_values is not None:
#                 # Check for invalid values
#                 invalid_mask = (rsi_values < 0) | (rsi_values > 100) | np.isnan(rsi_values)
                
#                 if invalid_mask.any():
#                     print(f"⚠️  Warning: Found {invalid_mask.sum()} invalid RSI values. Clipping to 0-100 range.")
#                     # Clip values to valid range
#                     rsi_values = np.clip(rsi_values, 0, 100)
                
#                 df["rsi"] = rsi_values
                
#                 # Additional validation check
#                 print(f"✅ RSI applied successfully. Range: {df['rsi'].min():.2f} - {df['rsi'].max():.2f}")
#             else:
#                 raise ValueError("RSI calculation returned None")
                
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
# import pandas as pd
# import numpy as np
# import ta  # pip install ta

# def apply_indicator(df, indicator: str, length: int = 14):
#     """
#     Applies the specified indicator to the DataFrame and returns the modified DataFrame.
#     Supports RSI, EMA, SMA, MACD.
#     """
#     indicator = indicator.lower()

#     try:
#         if indicator == "rsi":
#             rsi_indicator = ta.momentum.RSIIndicator(close=df["close"], window=length)
#             df["rsi"] = rsi_indicator.rsi()
#             # Ensure RSI is within 0-100
#             df["rsi"] = df["rsi"].clip(0, 100)
#             print(f"✅ RSI applied. Range: {df['rsi'].min():.2f} - {df['rsi'].max():.2f}")

#         elif indicator == "ema":
#             ema_indicator = ta.trend.EMAIndicator(close=df["close"], window=length)
#             df["ema"] = ema_indicator.ema_indicator()
#             print(f"✅ EMA applied. Latest: {df['ema'].iloc[-1]:.2f}")

#         elif indicator == "sma":
#             sma_indicator = ta.trend.SMAIndicator(close=df["close"], window=length)
#             df["sma"] = sma_indicator.sma_indicator()
#             print(f"✅ SMA applied. Latest: {df['sma'].iloc[-1]:.2f}")

#         elif indicator == "macd":
#             macd_indicator = ta.trend.MACD(close=df["close"])
#             df["macd"] = macd_indicator.macd()
#             df["macd_signal"] = macd_indicator.macd_signal()
#             df["macd_hist"] = macd_indicator.macd_diff()
#             print(f"✅ MACD applied. Latest: MACD={df['macd'].iloc[-1]:.2f}, Signal={df['macd_signal'].iloc[-1]:.2f}")

#         else:
#             raise ValueError(f"Indicator '{indicator}' not supported")

#         return df

#     except Exception as e:
#         print(f"❌ Failed to apply indicator '{indicator}': {e}")
#         return df


import pandas as pd
import numpy as np
import ta  # pip install ta

def apply_indicator(df, indicator: str, length: int = 14):
    """
    Applies the specified indicator to the DataFrame and returns the modified DataFrame.
    Supports RSI, EMA, SMA, MACD.
    For EMA, length can be a single int or a list of ints for multiple EMAs.
    """
    indicator = indicator.lower()

    try:
        if indicator == "rsi":
            rsi_indicator = ta.momentum.RSIIndicator(close=df["close"], window=length)
            df["rsi"] = rsi_indicator.rsi()
            df["rsi"] = df["rsi"].clip(0, 100)
            print(f"✅ RSI applied. Range: {df['rsi'].min():.2f} - {df['rsi'].max():.2f}")

        elif indicator == "ema":
            # Allow multiple EMAs if length is a list
            if isinstance(length, int):
                lengths = [length]
            else:
                lengths = length

            for l in lengths:
                ema_indicator = ta.trend.EMAIndicator(close=df["close"], window=l)
                df[f"ema_{l}"] = ema_indicator.ema_indicator()
                print(f"✅ EMA {l} applied. Latest: {df[f'ema_{l}'].iloc[-1]:.2f}")

        elif indicator == "sma":
            sma_indicator = ta.trend.SMAIndicator(close=df["close"], window=length)
            df["sma"] = sma_indicator.sma_indicator()
            print(f"✅ SMA applied. Latest: {df['sma'].iloc[-1]:.2f}")

        elif indicator == "macd":
            macd_indicator = ta.trend.MACD(close=df["close"])
            df["macd"] = macd_indicator.macd()
            df["macd_signal"] = macd_indicator.macd_signal()
            df["macd_hist"] = macd_indicator.macd_diff()
            print(f"✅ MACD applied. Latest: MACD={df['macd'].iloc[-1]:.2f}, Signal={df['macd_signal'].iloc[-1]:.2f}")

        else:
            raise ValueError(f"Indicator '{indicator}' not supported")

        return df

    except Exception as e:
        print(f"❌ Failed to apply indicator '{indicator}': {e}")
        return df