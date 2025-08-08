import time
import asyncio
import os
import operator
from .strategy_state import is_running, stop_strategy_flag
from .utils import get_candle_data, save_trade, save_trade_record
import pandas_ta as ta
from .indicators import apply_indicator
from .instrument_utils import get_instruments_from_openapi
from trades.strategy.optimization import OpenApiInstrumentReader
from log_stream import send_log, broadcast_trade_saved, broadcast_strategy_status

def evaluate_condition(df, condition, ltp=None):
    """Evaluates a single StrategyCondition dictionary against the DataFrame."""
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
            val = df[condition["left_indicator"]].iloc[-1] * condition.get("left_factor", 1)
            const = condition["constant_value"]
            result = op(val, const)
            print(f"\n📌 Condition: {condition['left_indicator'].upper()} {condition['operator']} {const}")
            print(f"🔎 Values: {val:.2f} {condition['operator']} {const} → {'✅ True' if result else '❌ False'}")
            return result

        # --- INDICATOR vs INDICATOR ---
        elif condition["comparison_type"] == "indicator_vs_indicator":
            left = df[condition["left_indicator"]].iloc[-1] * condition.get("left_factor", 1)
            right = df[condition["right_indicator"]].iloc[-1] * condition.get("right_factor", 1)
            result = op(left, right)
            print(f"\n📌 Condition: {condition['left_indicator'].upper()} {condition['operator']} {condition['right_indicator'].upper()}")
            print(f"🔎 Values: {left:.2f} {condition['operator']} {right:.2f} → {'✅ True' if result else '❌ False'}")
            return result

        # --- OHLC vs INDICATOR ---
        elif condition["comparison_type"] == "ohlc_vs_indicator":
            left = df[condition["left_ohlc"]].iloc[-condition.get("left_candle_offset", 1)] * condition.get("left_multiplier", 1)
            right = df[condition["right_indicator"]].iloc[-1] * condition.get("right_factor", 1)
            result = op(left, right)
            print(f"\n📌 Condition: {condition['left_ohlc'].upper()} {condition['operator']} {condition['right_indicator'].upper()}")
            print(f"🔎 Values: {left:.2f} {condition['operator']} {right:.2f} → {'✅ True' if result else '❌ False'}")
            return result

        # --- OHLC vs OHLC ---
        elif condition["comparison_type"] == "ohlc_vs_ohlc":
            left = df[condition["left_ohlc"]].iloc[-condition.get("left_candle_offset", 1)] * condition.get("left_multiplier", 1)
            right = df[condition["right_ohlc"]].iloc[-condition.get("right_candle_offset", 1)] * condition.get("right_multiplier", 1)
            result = op(left, right)
            print(f"\n📌 Condition: {condition['left_ohlc'].upper()} {condition['operator']} {condition['right_ohlc'].upper()}")
            print(f"🔎 Values: {left:.2f} {condition['operator']} {right:.2f} → {'✅ True' if result else '❌ False'}")
            return result

        # --- OHLC vs LTP ---
        # elif condition["comparison_type"] == "ohlc_vs_ltp":
        #     if ltp is None:
        #         raise ValueError("LTP is required for 'ohlc_vs_ltp' comparison type.")
        #     left = df[condition["left_ohlc"]].iloc[-condition.get("left_candle_offset", 1)] * condition.get("left_multiplier", 1)
        #     result = op(left, ltp)
        #     print(f"\n📌 Condition: {condition['left_ohlc'].upper()} {condition['operator']} LTP")
        #     print(f"🔎 Values: {left:.2f} {condition['operator']} {ltp:.2f} → {'✅ True' if result else '❌ False'}")
        #     return result
        elif condition["comparison_type"] == "ohlc_vs_ltp":
            if ltp is None:
                raise ValueError("LTP is required for 'ohlc_vs_ltp' comparison type.")

            candle_offset = condition.get("left_candle_offset", 1)
            multiplier = condition.get("left_multiplier", 1)
            ohlc_col = condition["left_ohlc"]

            # Calculate actual value
            raw_value = df[ohlc_col].iloc[-candle_offset]
            left = raw_value * multiplier
            result = op(left, ltp)

            # Detailed logging
            print(f"\n📌 Condition: {ohlc_col.upper()}[{candle_offset}] * {multiplier} {condition['operator']} LTP")
            print(f"🔎 Values: ({raw_value:.2f} * {multiplier}) = {left:.2f} {condition['operator']} {ltp:.2f} → {'✅ True' if result else '❌ False'}")

            return result


    except Exception as e:
        print(f"\n❌ Error evaluating condition: {condition} → {e}")
        return False


# def strategy_worker(payload, ltp_provider, credentials, service, user_data):
#     strategy_id = payload["strategy_id"]
#     symbol = f"{payload['index']}{payload['expiry']}{payload['strike_price']}{payload['option_type']}"
#     interval = payload["candle_duration"]
#     quantity = payload["quantity"]
#     trade_amount = payload['trade_amount']
#     target_profit = payload["target_profit"]
#     signal = "buy"
#     entry_price = 0
#     total_profit = 0
#     conditions = payload["conditions"]

#     instrument_reader = OpenApiInstrumentReader(os.getenv("NFO_DATA_URL"), [symbol])
#     instruments = instrument_reader.read_instruments()
#     print(instruments, "instruments")
#     if not instruments:
#         print(f"❌ No instrument found for symbol: {symbol}")
#         stop_strategy_flag(strategy_id)
#         return
#     token_model = instruments[0]
#     print(token_model.__dict__, "model_object")

#     print(f"\n🚀 Starting strategy [{strategy_id}]")
#     print(f"🧾 Symbol: {symbol}")
#     print(f"🛠️ Config → Candle Interval: {interval}, Quantity: {quantity}, Target Profit: ₹{target_profit:.2f}")
#     print(f"📋 Total Conditions: {len(conditions)}\n")

#     while is_running(strategy_id):
#         print(f"\n📈 Fetching candle data for: {symbol}")
#         df = get_candle_data(token=[symbol], exchange="NFO", interval=interval, days=1, credentials=credentials)

#         if df.empty:
#             print("⚠️ Candle data is empty. Retrying in 5 seconds...")
#             time.sleep(5)
#             continue

#         # Apply indicators
#         print("🛠️ Applying indicators...")
#         asyncio.run(send_log("🛠️ Applying indicators..."))
#         used_indicators = set()
#         for cond in conditions:
#             for ind_key in ["left_indicator", "right_indicator"]:
#                 ind = cond.get(ind_key)
#                 if ind and ind not in df.columns and ind not in used_indicators:
#                     try:
#                         count = cond.get("left_candle_count") or cond.get("right_candle_count") or 14
#                         df = apply_indicator(df, ind, count)
#                         used_indicators.add(ind)
#                         print(f"✅ Applied indicator: {ind}")
#                     except Exception as e:
#                         print(f"❌ Failed to apply indicator '{ind}': {e}")

#         df.dropna(inplace=True)
#         current_close = ltp_provider.fetch_ltp_data(token_model)
#         print(f"\n📊 Current Signal: {signal.upper()} | LTP: ₹{current_close:.2f} | Total PnL: ₹{total_profit:.2f}")
#         log_message = f"\n📊 Current Signal: {signal.upper()} | LTP: ₹{current_close:.2f} | Total PnL: ₹{total_profit:.2f}"
#         asyncio.run(send_log(log_message))

#         # Evaluate group of conditions
#         def evaluate_group(cond_type):
#             group = [c for c in conditions if c["type"] == cond_type]
#             if not group:
#                 return True

#             expr = ""
#             all_results = []
#             for i, cond in enumerate(group):
#                 try:
#                     result = evaluate_condition(df, cond, ltp=current_close)
#                     logic = cond.get("logic_operator")
#                     all_results.append((cond, result, logic))

#                     log_line = f"📌 Condition: "
#                     if cond.get("left_indicator"):
#                         log_line += f"{cond['left_indicator'].upper()} {cond['operator']} {cond.get('constant_value', '')}"
#                     elif cond.get("comparison_type") == "ohlc_vs_ltp":
#                         log_line += f"{cond['left_ohlc'].upper()}[{cond['left_candle_offset']}] {cond['operator']} LTP"
#                     else:
#                         log_line += f"Unknown"

#                     if logic:
#                         log_line += f" [{logic}]"
#                     print(log_line)

#                 except Exception as e:
#                     print(f"❌ Error evaluating condition: {cond} → {e}")
#                     return False

#             for i, (cond, result, logic) in enumerate(all_results):
#                 if i == 0:
#                     expr = str(result)
#                 else:
#                     prev_logic = all_results[i - 1][2]
#                     if not prev_logic:
#                         print(f"⚠️ Missing logic_operator in condition index {i}: {cond}")
#                         return False
#                     expr = f"({expr} {prev_logic.lower()} {result})"

#             try:
#                 print(f"🔎 Final Expression: {expr} → {eval(expr)}")
#                 return eval(expr)
#             except Exception as e:
#                 print(f"❌ Error evaluating logical expression: {expr} → {e}")
#                 return False

#         if signal == "buy":
#             if evaluate_group("pre_buy"):
#                 buy_cond = next((c for c in conditions if c["type"] == "buy"), None)
#                 if buy_cond:
#                     # if buy_cond["comparison_type"] == "spot":
#                     #     entry_price = current_close
#                     #     # actal buy
#                     #     lot_size = int(token_model.lotsize)
#                     #     print(lot_size, "lotsize")
#                     #     max_lots_affordable = int(trade_amount // (entry_price * lot_size))
#                     #     if max_lots_affordable < 1:
#                     #         print(f"❌ Insufficient capital to buy even 1 lot at ₹{entry_price:.2f}")
#                     #         stop_strategy_flag(strategy_id)
#                     #         break  # Stop the loop
#                     #     lots_to_trade = min(quantity, max_lots_affordable)
#                     #     actual_qty = lots_to_trade * lot_size
#                     #     print(f"🛒 Executing BUY for {lots_to_trade} lot(s) → Qty: {actual_qty}")
#                     if buy_cond["comparison_type"] == "spot":
#                         entry_price = current_close
#                         print(f"📈 Buy condition matched: SPOT | Entry price (LTP): ₹{entry_price:.2f}")

#                         lot_size = int(token_model.lotsize)
#                         print(f"📦 Lot size from token model: {lot_size}")

#                         max_lots_affordable = int(trade_amount // (entry_price * lot_size))
#                         print(f"💰 Max lots affordable with ₹{trade_amount}: {max_lots_affordable} lot(s)")

#                         if max_lots_affordable < 1:
#                             print(f"❌ Insufficient capital to buy even 1 lot at ₹{entry_price:.2f} (Trade Amt: ₹{trade_amount})")
#                             stop_strategy_flag(strategy_id)
#                             break  # Stop the loop

#                         lots_to_trade = min(quantity, max_lots_affordable)
#                         actual_qty = lots_to_trade * lot_size

#                         print(f"🛒 Executing BUY → Requested Qty: {quantity} lot(s) | Executing: {lots_to_trade} lot(s) → Total Qty: {actual_qty}")

#                         # order_id, order_details = service.place_order(
#                         #     symbol=token_model["symbol"],
#                         #     token=token_model["token"],
#                         #     transaction="BUY",
#                         #     ordertype="MARKET",
#                         #     price=entry_price,
#                         #     quantity=actual_qty
#                         # )
#                         # if order_details.get("status") == "rejected":
#                         #     print(f"Buy order was rejected: {order_details.get('text')}")
#                         #     signal = "buy"
#                         #     continue

#                         signal = "sell"
#                         save_trade(signal_type="BUY",price=entry_price,token_value=token_model.token,user_id=user_data["user_id"])
#                         print(f"\n🟢 BUY signal (SPOT) executed at ₹{entry_price:.2f}")
#                     elif buy_cond["comparison_type"] == "ohlc_vs_ltp":
#                         if evaluate_condition(df, buy_cond, ltp=current_close):
#                             entry_price = current_close
#                             lot_size = int(token_model.lotsize)
#                             max_lots_affordable = int(trade_amount // (entry_price * lot_size))
#                             if max_lots_affordable < 1:
#                                 print(f"❌ Insufficient capital to buy even 1 lot at ₹{entry_price:.2f}")
#                                 stop_strategy_flag(strategy_id)
#                                 break  
#                             lots_to_trade = min(quantity, max_lots_affordable)
#                             actual_qty = lots_to_trade * lot_size
#                             print(f"🛒 Executing BUY for {lots_to_trade} lot(s) → Qty: {actual_qty}")
#                             # order_id, order_details = service.place_order(
#                             #     symbol=token_model["symbol"],
#                             #     token=token_model["token"],
#                             #     transaction="BUY",
#                             #     ordertype="MARKET",
#                             #     price=entry_price,
#                             #     quantity=actual_qty
#                             # )
#                             # if order_details.get("status") == "rejected":
#                             #     print(f"Buy order was rejected: {order_details.get('text')}")
#                             #     signal = "buy"
#                             #     continue
#                             signal = "sell"
#                             save_trade(signal_type="BUY",price=entry_price,token_value=token_model.token,user_id=user_data["user_id"])
#                             print(f"\n🟢 BUY signal (OHLC vs LTP) executed at ₹{entry_price:.2f}")
#                         else:
#                             print("⏳ Buy condition (ohlc_vs_ltp) not met. Waiting...")
#                     else:
#                         print(f"❌ Unsupported buy comparison_type: {buy_cond['comparison_type']}")
#                 else:
#                     print("⚠️ No BUY condition found.")
#             else:
#                 print("⏳ Pre-buy condition not met. Waiting...")

#         elif signal == "sell":
#             if evaluate_group("pre_sell"):
#                 target_cond = next((c for c in conditions if c["type"] == "target"), None)
#                 sl_cond = next((c for c in conditions if c["type"] == "stop_loss"), None)
#                 sell_cond = next((c for c in conditions if c["type"] == "sell"), None)

#                 target_hit = False
#                 sl_hit = False
#                 sell_match = False

#                 if target_cond:
#                     target_price = (
#                         entry_price + target_cond["sl_tp_value"]
#                         if target_cond["value_type"] == "points"
#                         else entry_price + (entry_price * target_cond["sl_tp_value"] / 100)
#                     )
#                     if current_close >= target_price:
#                         target_hit = True
#                         print(f"🎯 Target reached at ₹{current_close:.2f} (Target: ₹{target_price:.2f})")

#                 if sl_cond:
#                     sl_price = (
#                         entry_price - sl_cond["sl_tp_value"]
#                         if sl_cond["value_type"] == "points"
#                         else entry_price - (entry_price * sl_cond["sl_tp_value"] / 100)
#                     )
#                     if current_close <= sl_price:
#                         sl_hit = True
#                         print(f"🛑 Stop-loss hit at ₹{current_close:.2f} (SL: ₹{sl_price:.2f})")

#                 if sell_cond:
#                     if sell_cond["comparison_type"] == "spot":
#                         sell_match = True
#                         print(f"\n🟢 SELL signal (SPOT) executed at ₹{current_close:.2f}")
#                     elif sell_cond["comparison_type"] == "ohlc_vs_ltp":
#                         sell_match = evaluate_condition(df, sell_cond, ltp=current_close)
#                     if sell_match:
#                         print(f"\n🟢 SELL signal (ohlc_vs_ltp) executed at ₹{current_close:.2f}")

#                 if target_hit or sl_hit or sell_match:
#                     print(f"💼 Executing SELL for Qty: {actual_qty}")
#                     # order_id, order_details = service.place_order(
#                     #     symbol=token_model["symbol"],
#                     #     token=token_model["token"],
#                     #     transaction="SELL",
#                     #     ordertype="MARKET",
#                     #     price=current_close,
#                     #     quantity=actual_qty
#                     # )
#                     # if order_details.get("status") == "rejected":
#                     #     print(f"❌ Sell order was rejected: {order_details.get('text')}")
#                     #     signal = "sell"
#                     #     continue
#                     pnl = (current_close - entry_price) * actual_qty
#                     total_profit += pnl
#                     status = "🟢 Profit" if pnl >= 0 else "🔻 Loss"
#                     print(f"\n🔴 SELL executed at ₹{current_close:.2f} → {status}: ₹{abs(pnl):.2f} → Total PnL: ₹{total_profit:.2f}")
#                     signal = "buy"
#                     save_trade(signal_type="SELL",price=current_close,token_value=token_model.token,user_id=user_data["user_id"])


#                 else:
#                     print("⏳ No sell condition met (target/SL/sell). Waiting...")
#             else:
#                 print("⏳ Pre-sell condition not met. Waiting...")

#         if total_profit >= target_profit:
#             print(f"\n🎯 Target profit reached: ₹{total_profit:.2f}. Stopping strategy.")
#             stop_strategy_flag(strategy_id)
#             break

#         time.sleep(5)

#     print(f"\n⏹️ Strategy [{strategy_id}] completed. Final Profit: ₹{total_profit:.2f}\n")

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

    while is_running(strategy_id):
        asyncio.run(broadcast_strategy_status({"strategy_id": strategy_id, "is_running":True}))
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
        used_indicators = set()
        for cond in conditions:
            for ind_key in ["left_indicator", "right_indicator"]:
                ind = cond.get(ind_key)
                if ind and ind not in df.columns and ind not in used_indicators:
                    try:
                        count = cond.get("left_candle_count") or cond.get("right_candle_count") or 14
                        df = apply_indicator(df, ind, count)
                        used_indicators.add(ind)
                        msg = f"✅ Applied indicator: {ind}"
                        print(msg)
                        asyncio.run(send_log(msg))
                    except Exception as e:
                        error_msg = f"❌ Failed to apply indicator '{ind}': {e}"
                        print(error_msg)
                        asyncio.run(send_log(error_msg))

        df.dropna(inplace=True)
        current_close = ltp_provider.fetch_ltp_data(token_model)
        status_msg = (
            f"\n📊 Current Signal: {signal.upper()} | LTP: ₹{current_close:.2f} | Total PnL: ₹{total_profit:.2f}"
        )
        print(status_msg)
        asyncio.run(send_log(status_msg))

        # ----------- Group Condition Evaluation -------------
        def evaluate_group(cond_type):
            group = [c for c in conditions if c["type"] == cond_type]
            if not group:
                return True

            expr = ""
            all_results = []
            for i, cond in enumerate(group):
                try:
                    result = evaluate_condition(df, cond, ltp=current_close)
                    logic = cond.get("logic_operator")
                    all_results.append((cond, result, logic))

                    log_line = "📌 Condition: "
                    if cond.get("left_indicator"):
                        log_line += f"{cond['left_indicator'].upper()} {cond['operator']} {cond.get('constant_value', '')}"
                    elif cond.get("comparison_type") == "ohlc_vs_ltp":
                        log_line += f"{cond['left_ohlc'].upper()}[{cond['left_candle_offset']}] {cond['operator']} LTP"
                    else:
                        log_line += f"Unknown"
                    if logic:
                        log_line += f" [{logic}]"
                    print(log_line)
                    asyncio.run(send_log(log_line))
                except Exception as e:
                    error_msg = f"❌ Error evaluating condition: {cond} → {e}"
                    print(error_msg)
                    asyncio.run(send_log(error_msg))
                    return False

            for i, (cond, result, logic) in enumerate(all_results):
                if i == 0:
                    expr = str(result)
                else:
                    prev_logic = all_results[i - 1][2]
                    if not prev_logic:
                        warn_msg = f"⚠️ Missing logic_operator in condition index {i}: {cond}"
                        print(warn_msg)
                        asyncio.run(send_log(warn_msg))
                        return False
                    expr = f"({expr} {prev_logic.lower()} {result})"

            try:
                final_eval = f"🔎 Final Expression: {expr} → {eval(expr)}"
                print(final_eval)
                asyncio.run(send_log(final_eval))
                return eval(expr)
            except Exception as e:
                eval_error = f"❌ Error evaluating logical expression: {expr} → {e}"
                print(eval_error)
                asyncio.run(send_log(eval_error))
                return False

        # ----------- Buy Logic -------------
        if signal == "buy":
            if evaluate_group("pre_buy"):
                buy_cond = next((c for c in conditions if c["type"] == "buy"), None)
                if buy_cond:
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
                asyncio.run(send_log("⏳ Pre-buy condition not met. Waiting..."))

        # ----------- Sell Logic -------------
        elif signal == "sell":
            if evaluate_group("pre_sell"):
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
