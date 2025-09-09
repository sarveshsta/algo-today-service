import time
import asyncio
import os
import operator
import pandas as pd
from .strategy_state import is_running, stop_strategy_flag
from .utils import get_candle_data, save_trade, save_trade_record, save_strategy_payload
import pandas_ta as ta
from .indicators import apply_indicator
from .instrument_utils import get_instruments_from_openapi
from trades.strategy.optimization import OpenApiInstrumentReader
from log_stream import send_log, broadcast_trade_saved, broadcast_strategy_status

def normalize_indicator_name(indicator, candle_count):
    # Map short names to real df column names
    ind = indicator.lower()
    if ind in ["ema", "sma", "rsi"]:
        return f"{ind}_{candle_count}"
    elif ind == "macd":
        return "macd_line"  # or "macd_signal" depending on what you want to compare
    return ind

def apply_missing_indicators(df, conditions):
    """
    Automatically applies all missing indicators from conditions to the DataFrame.
    EMA, SMA, RSI, MACD supported.
    """
    import ta
    used_indicators = set()

    for cond in conditions:
        for ind_key, count_key in [("left_indicator", "left_candle_count"), ("right_indicator", "right_candle_count")]:
            ind = cond.get(ind_key)
            count = cond.get(count_key) or 14
            if ind:
                col_name = f"{ind}_{count}" if ind.lower() in ["ema", "sma", "rsi"] else ind
                if col_name not in df.columns and col_name not in used_indicators:
                    # Apply indicator
                    if ind.lower() == "rsi":
                        df[col_name] = ta.momentum.RSIIndicator(close=df["close"], window=count).rsi().clip(0, 100)
                    elif ind.lower() == "ema":
                        df[col_name] = ta.trend.EMAIndicator(close=df["close"], window=count).ema_indicator()
                    elif ind.lower() == "sma":
                        df[col_name] = ta.trend.SMAIndicator(close=df["close"], window=count).sma_indicator()
                    elif ind.lower() == "macd":
                        macd = ta.trend.MACD(close=df["close"])
                        df["macd_line"] = macd.macd()
                        df["macd_signal"] = macd.macd_signal()
                        df["macd_hist"] = macd.macd_diff()
                    used_indicators.add(col_name)
                    msg = f"✅ Applied indicator: {col_name}"
                    print(msg)
                    asyncio.run(send_log(msg))
    return df


def evaluate_condition(df, condition, ltp=None):
    """Evaluates a single StrategyCondition dictionary against the DataFrame and logs details."""
    op_map = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
    }

    op = op_map[condition["operator"]]

    try:
        # --- INDICATOR vs VALUE ---
        if condition["comparison_type"] == "indicator_vs_value":
            col = normalize_indicator_name(condition["left_indicator"], condition.get("left_candle_count", 14))
            val = df[col].iloc[-1] * condition.get("left_factor", 1)
            const = condition["constant_value"]
            result = op(val, const)
            indicator_vs_value_msg = f"📌 Condition: {col.upper()} {condition['operator']} {const} → {val:.2f} {result}"
            print(indicator_vs_value_msg)
            asyncio.run(send_log(indicator_vs_value_msg))
            return result

        # --- INDICATOR vs INDICATOR ---
        elif condition["comparison_type"] == "indicator_vs_indicator":
            left_col = normalize_indicator_name(condition["left_indicator"], condition.get("left_candle_count", 14))
            right_col = normalize_indicator_name(condition["right_indicator"], condition.get("right_candle_count", 14))
            left = df[left_col].iloc[-1] * condition.get("left_factor", 1)
            right = df[right_col].iloc[-1] * condition.get("right_factor", 1)
            result = op(left, right)
            indicator_vs_indicator_msg = f"📌 Condition: {left_col.upper()} {condition['operator']} {right_col.upper()} → {left:.2f} vs {right:.2f} {result}"
            print(indicator_vs_indicator_msg)
            asyncio.run(send_log(indicator_vs_indicator_msg))
            return result

        # --- OHLC vs INDICATOR ---
        elif condition["comparison_type"] == "ohlc_vs_indicator":
            right_col = normalize_indicator_name(condition["right_indicator"], condition.get("right_candle_count", 14))
            left = df[condition["left_ohlc"]].iloc[-condition.get("left_candle_offset", 1)] * condition.get("left_multiplier", 1)
            right = df[right_col].iloc[-1] * condition.get("right_factor", 1)
            result = op(left, right)
            ohlc_vs_indicator_msg = f"📌 Condition: {condition['left_ohlc'].upper()} {condition['operator']} {right_col.upper()} → {left:.2f} vs {right:.2f} {result}"
            print(ohlc_vs_indicator_msg)
            asyncio.run(send_log(ohlc_vs_indicator_msg))
            return result

        # --- OHLC vs OHLC ---
        elif condition["comparison_type"] == "ohlc_vs_ohlc":
            left = df[condition["left_ohlc"]].iloc[-condition.get("left_candle_offset", 1)] * condition.get("left_multiplier", 1)
            right = df[condition["right_ohlc"]].iloc[-condition.get("right_candle_offset", 1)] * condition.get("right_multiplier", 1)
            result = op(left, right)
            ohlc_vs_ohlc_msg = f"📌 Condition: {condition['left_ohlc'].upper()} {condition['operator']} {condition['right_ohlc'].upper()} → {left:.2f} vs {right:.2f} {result}"
            print(ohlc_vs_ohlc_msg)
            asyncio.run(send_log(ohlc_vs_ohlc_msg))
            return result

        # --- OHLC vs LTP ---
        elif condition["comparison_type"] == "ohlc_vs_ltp":
            if ltp is None:
                raise ValueError("LTP is required for 'ohlc_vs_ltp' comparison type.")
            left = df[condition["left_ohlc"]].iloc[-condition.get("left_candle_offset", 1)] * condition.get("left_multiplier", 1)
            result = op(left, ltp)
            ohlc_vs_ltp_msg = f"📌 Condition: {condition['left_ohlc'].upper()} {condition['operator']} LTP({ltp}) → {left:.2f} {result}"
            print(ohlc_vs_ltp_msg)
            asyncio.run(send_log(ohlc_vs_ltp_msg))
            return result

        # --- SPOT ---
        elif condition["comparison_type"] == "spot":
            spot_msg = "📌 Condition: SPOT → True"
            print(spot_msg)
            asyncio.run(send_log(spot_msg))
            return True

    except Exception as e:
        error_msg = f"❌ Error evaluating condition: {condition} → {e}"
        print(error_msg)
        asyncio.run(send_log(error_msg))
        return False


def evaluate_group(df, conditions, cond_type, ltp=None):
    """Evaluates a group of conditions using their logic operators, with detailed logging."""
    group = [c for c in conditions if c["type"] == cond_type]
    if not group:
        return True

    expr = ""
    all_results = []
    group_cond_msg = f"\n🔍 Evaluating {cond_type.upper()} conditions..."
    print(group_cond_msg)
    asyncio.run(send_log(group_cond_msg))
    for i, cond in enumerate(group):
        result = evaluate_condition(df, cond, ltp=ltp)
        logic = cond.get("logic_operator")
        all_results.append((cond, result, logic))

    for i, (cond, result, logic) in enumerate(all_results):
        if i == 0:
            expr = str(result)
        else:
            prev_logic = all_results[i - 1][2]
            if not prev_logic:
                missing_logic_operator_msg = f"⚠️ Missing logic_operator in condition index {i}: {cond}"
                print(missing_logic_operator_msg)
                asyncio.run(send_log(missing_logic_operator_msg))
                return False
            expr = f"({expr} {prev_logic.lower()} {result})"

    try:
        final_result = eval(expr)
        final_exp_msg = f"🧮 Final Expression: {expr} → {final_result}"
        print(final_exp_msg)
        asyncio.run(send_log(final_exp_msg))
        return final_result
    except Exception as e:
        error_msg = f"❌ Error evaluating logical expression: {expr} → {e}"
        print(error_msg)
        asyncio.run(send_log(error_msg))
        return False



def strategy_worker(payload, ltp_provider, credentials, service, user_data):
    strategy_id = payload["strategy_id"]
    symbol = f"{payload['index']}{payload['expiry']}{payload['strike_price']}{payload['option_type']}"
    interval = payload["candle_duration"]
    quantity = payload["quantity"]
    trade_amount = payload['trade_amount']
    target_profit = payload["target_profit"]
    signal = "buy"
    entry_price = 0
    total_profit = 0
    conditions = payload["conditions"]

    instrument_reader = OpenApiInstrumentReader(os.getenv("NFO_DATA_URL"), [symbol])
    instruments = instrument_reader.read_instruments()
    print(instruments, "instruments")

    if not instruments:
        msg = f"❌ No instrument found for symbol: {symbol}"
        print(msg)
        asyncio.run(send_log(msg))
        stop_strategy_flag(strategy_id)
        return

    token_model = instruments[0]
    print(token_model.__dict__, "model_object")

    start_msg = (
        f"\n🚀 Starting strategy [{strategy_id}]\n"
        f"🧾 Symbol: {symbol}\n"
        f"🛠️ Config → Candle Interval: {interval}, Quantity: {quantity}, Target Profit: ₹{target_profit:.2f}\n"
        f"📋 Total Conditions: {len(conditions)}\n"
    )
    print(start_msg)
    asyncio.run(send_log(start_msg))
    save_strategy_payload(user_data['user_id'], payload)
    while is_running(strategy_id):
        # asyncio.run(broadcast_strategy_status({"strategy_id": strategy_id, "is_running":True}))
        msg = f"\n📈 Fetching candle data for: {symbol}"
        print(msg)
        asyncio.run(send_log(msg))

        df = get_candle_data(token=[symbol], exchange="NFO", interval=interval, days=1, credentials=credentials)
        if df.empty:
            retry_msg = "⚠️ Candle data is empty. Retrying in 5 seconds..."
            print(retry_msg)
            asyncio.run(send_log(retry_msg))
            time.sleep(5)
            continue
        print("🛠️ Applying indicators...")
        asyncio.run(send_log("🛠️ Applying indicators..."))
        df = apply_missing_indicators(df, conditions)

        

        df.dropna(inplace=True)
        current_close = ltp_provider.fetch_ltp_data(token_model)
        status_msg = (
            f"\n📊 Current Signal: {signal.upper()} | LTP: ₹{current_close:.2f} | Total PnL: ₹{total_profit:.2f}"
        )
        print(status_msg)
        asyncio.run(send_log(status_msg))

        # ----------- Buy Logic -------------
        if signal == "buy":
            if evaluate_group(df, conditions, "pre_buy", ltp=current_close):
                buy_cond = next((c for c in conditions if c["type"] == "buy"), None)
                if buy_cond:
                    print("Evaluating BUY conditions...")
                    if buy_cond["comparison_type"] == "spot":
                        entry_price = current_close
                        msg = f"📈 Buy condition matched: SPOT | Entry price (LTP): ₹{entry_price:.2f}"
                        print(msg)
                        asyncio.run(send_log(msg))

                        lot_size = int(token_model.lotsize)
                        max_lots_affordable = int(trade_amount // (entry_price * lot_size))

                        if max_lots_affordable < 1:
                            err = f"❌ Insufficient capital to buy even 1 lot at ₹{entry_price:.2f} (Trade Amt: ₹{trade_amount})"
                            print(err)
                            asyncio.run(send_log(err))
                            stop_strategy_flag(strategy_id)
                            break

                        lots_to_trade = min(quantity, max_lots_affordable)
                        actual_qty = lots_to_trade * lot_size

                        buy_msg = f"🛒 Executing BUY → Requested: {quantity} lot(s) | Executing: {lots_to_trade} lot(s) → Qty: {actual_qty}"
                        print(buy_msg)
                        asyncio.run(send_log(buy_msg))
                        # order_id, order_details = service.place_order(
                        #     symbol=token_model["symbol"],
                        #     token=token_model["token"],
                        #     transaction="BUY",
                        #     ordertype="MARKET",
                        #     price=entry_price,
                        #     quantity=actual_qty
                        # )
                        # if order_details.get("status") == "rejected":
                        #     print(f"Buy order was rejected: {order_details.get('text')}")
                        #     signal = "buy"
                        #     continue

                        signal = "sell"
                        save_trade(signal_type="BUY",
                                   quantity=actual_qty, 
                                   symbol=symbol,
                                   price=entry_price, 
                                   token_value=token_model.token, 
                                   user_id=user_data["user_id"])
                        save_trade_record(
                                          symbol=symbol, 
                                          quantity=actual_qty, 
                                          trade_type="BUY",
                                          user_id=user_data["user_id"],
                                          ltp=current_close,
                                          pnl=total_profit,
                                          order_type="NRML",
                                          strategy_id=strategy_id)
                        asyncio.run(send_log(f"🟢 BUY executed at ₹{entry_price:.2f}"))
                        asyncio.run(broadcast_trade_saved({"symbol": symbol, "trade_type": "BUY"}))
                    elif buy_cond["comparison_type"] == "ohlc_vs_ltp":
                        if evaluate_condition(df, buy_cond, ltp=current_close):
                            entry_price = current_close
                            lot_size = int(token_model.lotsize)
                            max_lots_affordable = int(trade_amount // (entry_price * lot_size))
                            if max_lots_affordable < 1:
                                err = f"❌ Insufficient capital to buy even 1 lot at ₹{entry_price:.2f}"
                                print(err)
                                asyncio.run(send_log(err))
                                stop_strategy_flag(strategy_id)
                                break

                            lots_to_trade = min(quantity, max_lots_affordable)
                            actual_qty = lots_to_trade * lot_size
                            print(f"🛒 Executing BUY for {lots_to_trade} lot(s) → Qty: {actual_qty}")
                            # order_id, order_details = service.place_order(
                            #     symbol=token_model["symbol"],
                            #     token=token_model["token"],
                            #     transaction="BUY",
                            #     ordertype="MARKET",
                            #     price=entry_price,
                            #     quantity=actual_qty
                            # )
                            # if order_details.get("status") == "rejected":
                            #     print(f"Buy order was rejected: {order_details.get('text')}")
                            #     signal = "buy"
                            #     continue
                            signal = "sell"
                            save_trade(signal_type="BUY", 
                                        quantity=actual_qty, 
                                        symbol=symbol,
                                       price=entry_price, 
                                       token_value=token_model.token, 
                                       user_id=user_data["user_id"])
                            save_trade_record(
                                          symbol=symbol, 
                                          quantity=actual_qty, 
                                          trade_type="BUY",
                                          user_id=user_data["user_id"],
                                          ltp=current_close,
                                          pnl=total_profit,
                                          order_type="NRML",
                                          strategy_id=strategy_id)
                            asyncio.run(send_log(f"🟢 BUY (ohlc_vs_ltp) executed at ₹{entry_price:.2f}"))
                            asyncio.run(broadcast_trade_saved({"symbol": symbol, "trade_type": "BUY"}))
                        else:
                            asyncio.run(send_log("⏳ Buy condition (ohlc_vs_ltp) not met. Waiting..."))
                    else:
                        msg = f"❌ Unsupported buy comparison_type: {buy_cond['comparison_type']}"
                        print(msg)
                        asyncio.run(send_log(msg))
                else:
                    asyncio.run(send_log("⚠️ No BUY condition found."))
            else:
                print("⏳ Pre-buy condition not met. Waiting...")
                asyncio.run(send_log("⏳ Pre-buy condition not met. Waiting..."))

        # ----------- Sell Logic -------------
        elif signal == "sell":
            if evaluate_group(df, conditions, "pre_sell", ltp=current_close):
                target_cond = next((c for c in conditions if c["type"] == "target"), None)
                sl_cond = next((c for c in conditions if c["type"] == "stop_loss"), None)
                sell_cond = next((c for c in conditions if c["type"] == "sell"), None)

                target_hit = sl_hit = sell_match = False

                if target_cond:
                    target_price = (
                        entry_price + target_cond["sl_tp_value"]
                        if target_cond["value_type"] == "points"
                        else entry_price + (entry_price * target_cond["sl_tp_value"] / 100)
                    )
                    if current_close >= target_price:
                        target_hit = True
                        asyncio.run(send_log(f"🎯 Target reached at ₹{current_close:.2f} (Target: ₹{target_price:.2f})"))

                if sl_cond:
                    sl_price = (
                        entry_price - sl_cond["sl_tp_value"]
                        if sl_cond["value_type"] == "points"
                        else entry_price - (entry_price * sl_cond["sl_tp_value"] / 100)
                    )
                    if current_close <= sl_price:
                        sl_hit = True
                        asyncio.run(send_log(f"🛑 Stop-loss hit at ₹{current_close:.2f} (SL: ₹{sl_price:.2f})"))

                if sell_cond:
                    if sell_cond["comparison_type"] == "spot":
                        sell_match = True
                    elif sell_cond["comparison_type"] == "ohlc_vs_ltp":
                        sell_match = evaluate_condition(df, sell_cond, ltp=current_close)
                    if sell_match:
                        asyncio.run(send_log(f"🟢 SELL signal matched at ₹{current_close:.2f}"))

                if target_hit or sl_hit or sell_match:
                    # order_id, order_details = service.place_order(
                    #     symbol=token_model["symbol"],
                    #     token=token_model["token"],
                    #     transaction="SELL",
                    #     ordertype="MARKET",
                    #     price=current_close,
                    #     quantity=actual_qty
                    # )
                    # if order_details.get("status") == "rejected":
                    #     print(f"❌ Sell order was rejected: {order_details.get('text')}")
                    #     signal = "sell"
                    #     continue
                    pnl = (current_close - entry_price) * actual_qty
                    total_profit += pnl
                    status = "🟢 Profit" if pnl >= 0 else "🔻 Loss"
                    msg = f"🔴 SELL at ₹{current_close:.2f} → {status}: ₹{abs(pnl):.2f} | Total PnL: ₹{total_profit:.2f}"
                    print(msg)
                    asyncio.run(send_log(msg))
                    signal = "buy"
                    save_trade(signal_type="SELL", 
                                quantity=actual_qty, 
                                symbol=symbol,
                               price=current_close, 
                               token_value=token_model.token, 
                               user_id=user_data["user_id"])
                    save_trade_record(
                                    symbol=symbol, 
                                    quantity=actual_qty, 
                                    trade_type="SELL",
                                    user_id=user_data["user_id"],
                                    ltp=current_close,
                                    pnl=total_profit,
                                    order_type="NRML",
                                    strategy_id=strategy_id)
                    asyncio.run(broadcast_trade_saved({"symbol": symbol, "trade_type": "SELL"}))
                else:
                    asyncio.run(send_log("⏳ No sell condition met (target/SL/sell). Waiting..."))
            else:
                asyncio.run(send_log("⏳ Pre-sell condition not met. Waiting..."))

        if total_profit >= target_profit:
            final_msg = f"\n🎯 Target profit reached: ₹{total_profit:.2f}. Stopping strategy."
            print(final_msg)
            asyncio.run(send_log(final_msg))
            stop_strategy_flag(strategy_id)
            break

        time.sleep(5)

    end_msg = f"\n⏹️ Strategy [{strategy_id}] completed. Final Profit: ₹{total_profit:.2f}\n"
    print(end_msg)
    asyncio.run(send_log(end_msg))
