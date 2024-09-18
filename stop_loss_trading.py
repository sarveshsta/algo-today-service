# def save_trade(new_trade: TradeDetails):
                    #     global db
                    #     db.add(new_trade)
                    #     db.commit()
                    #     db.refresh(new_trade)
                    #     return new_trade

                    # def initialize_db():
                    #     global db
                    #     db = SessionLocal()
                    
                    # initialize_db()

                    # if signal == Signal.BUY:
                    #     self.indicator.price = self.indicator.price
                    #     self.indicator.stop_loss_price = self.indicator.price * constant.STOP_LOSS_MULTIPLIER
                    #     logger.info(
                    #         f"Trade BOUGHT at {self.indicator.price} in {index_info[0]} with SL={self.indicator.stop_loss_price}"
                    #     )
                        
                    #     if self.parameters_amount[index] == 0:
                    #         self.trading_quantity = self.parameters[index]
                            
                    #     else:
                    #         for instrument in self.instruments:
                    #             if instrument.symbol == index:
                    #                 self.lotsize = int(instrument.lotsize)
                    #                 self.token_id = instrument.token

                    #         amount = self.parameters_amount[index]
                    #         number_of_stocks = int(amount / (self.indicator.price * self.lotsize))
                    #         quantity = self.lotsize * number_of_stocks
                    #         self.trading_quantity = quantity
                    #         logger.info(f"Trade Quantity for {index} - {quantity}")
                           
                    #     current_time = datetime.now()

                        # new_trade = TradeDetails(
                        #     user_id=1,
                        #     signal="BUY",
                        #     price=self.indicator.price,
                        #     trade_time=current_time,
                        #     token_id=self.token_id
                        # ) 

                        # saved_trade =save_trade(new_trade)
                        # print(f"#############{saved_trade}###############")
                        # self.indicator.order_id, trade_book_full_response = await async_return(
                        #         self.data_provider.place_order(
                        #             index_info[0],
                        #             index_info[1],
                        #             "BUY",
                        #             "MARKET",
                        #             self.indicator.price,
                        #             self.trading_quantity,
                        #         )
                        #     )
                        
                        

                        # self.buying_price = float(trade_book_full_response["fillprice"])

                        # self.indicator.price = float(trade_book_full_response["fillprice"])
                        # self.indicator.stop_loss_price = round(self.indicator.price * 0.95, 2)
                        # logger.info(
                        #     f"Trade BOUGHT at {float(trade_book_full_response['fillprice'])} in {index_info[0]} with SL={self.indicator.stop_loss_price}"
                        # )

                    # elif signal == Signal.SELL:
                    #     # self.indicator.price, self.indicator.stop_loss_price = 0, 0
                    #     # logger.info(f"TRADE SOLD at {self.indicator.price} in {index_info[0]}")
                        

                    #     self.indicator.order_id, trade_book_full_response = await async_return(
                    #         self.data_provider.place_order(
                    #             index_info[0],
                    #             index_info[1],
                    #             "SELL",
                    #             "MARKET",
                    #             self.indicator.price,
                    #             self.trading_quantity,
                    #         )
                    #     )
                    #     self.indicator.price, self.indicator.stop_loss_price = 0, 0
                    #     logger.info(f"TRADE SOLD at {float(trade_book_full_response['fillprice'])} in {index_info[0]}")
                    #     self.current_profit += (float(trade_book_full_response['fillprice'] - self.buying_price) * self.trading_quantity)

                    # if not self.indicator.waiting_for_buy:
                    #     order_status, text = await async_return(self.data_provider.check_order_status(self.indicator.uniqueOrderId))
                    #     logger.info(f"order_status: {order_status}, message: {text}")

                    #     if order_status.lower() == 'complete':
                    #         self.indicator.waiting_for_buy = True
                    #         self.indicator.to_buy = False
                    #         self.indicator.to_modify = False
                    #         self.indicator.waiting_to_modify = False
                    #         logger.info("Stop-loss has been triggered")

                    # if signal == Signal.BUY:

                    #     self.indicator.order_id, trade_book_full_response = await async_return(self.data_provider.place_order(index_info[0], index_info[1], "BUY", "MARKET", self.indicator.price, self.parameters[index]))
                    #     self.indicator.price = float(trade_book_full_response['fillprice'])

                    #     await asyncio.sleep(1)
                    #     self.indicator.order_id, order_book_full_response = await async_return(self.data_provider.get_order_book(self.indicator.order_id))
                    #     self.indicator.uniqueOrderId = order_book_full_response['uniqueorderid']

                    #     logger.info(f"We got buying price at {self.indicator.price}")

                    #     if self.indicator.order_id:
                    #         logger.info(f"Market price at which we bought is {price}")
                    #         self.indicator.order_id, trade_book_full_response = await async_return(self.data_provider.place_stoploss_limit_order(index_info[0], index_info[1], self.parameters[index], (self.indicator.price*0.95), (self.indicator.price*0.90)))
                    #         self.indicator.stop_loss_price = self.indicator.price * 0.95
                    #         await asyncio.sleep(1)
                    #         self.indicator.order_id, order_book_full_response = await async_return(self.data_provider.get_order_book(self.indicator.order_id))
                    #         self.indicator.uniqueOrderId = order_book_full_response['uniqueorderid']
                    #         logger.info(f"STOPP_LOSS added, {self.indicator.order_id}")

                    #     logger.info(f"Order Status: {self.indicator.order_id} {trade_book_full_response}")

                    # elif signal == Signal.MODIFY:
                    #     logger.info(f"Order Status: {index_info} {Signal.MODIFY}")
                    #     self.indicator.order_id, trade_book_full_response = await async_return(self.data_provider.modify_stoploss_limit_order(index_info[0], index_info[1], self.parameters[index], (self.indicator.price), (self.indicator.price*0.95) , self.indicator.order_id))

                    #     self.indicator.order_id, order_book_full_response = await async_return(self.data_provider.get_order_book(self.indicator.order_id))
                    #     self.indicator.uniqueOrderId = order_book_full_response['uniqueorderid']

                    #     logger.info(f"Order Status: {self.indicator.order_id} {trade_book_full_response}")

                    # if not self.indicator.waiting_for_buy:
                    #     order_status, text = await async_return(self.data_provider.check_order_status(self.indicator.uniqueOrderId))
                    #     logger.info(f"order_status: {order_status}, message: {text}")

                    #     if order_status.lower() == 'complete':
                    #         self.indicator.waiting_for_buy = True
                    #         self.indicator.to_buy = False
                    #         self.indicator.to_modify = False
                    #         self.indicator.waiting_to_modify = False
                    #         logger.info("Stop-loss has been triggered")




    # # this is our main strategy function
    # def check_indicators(self, data: pd.DataFrame, passed_token: Token, ltp_value: float, index: int = 0):
    #     ltp = ltp_value

    #     token = str(passed_token).split(":")[-1]  # this is actually symbol written as FINNIFTY23JUL2423500CE\

    #     symbol_token = str(passed_token).split(":")[
    #         1
    #     ]  # a five digit integer number to represent the actual token number for the symbol
    #     index_info = [token, symbol_token, ltp]
    #     try:
    #         # checking for pre buying condition
    #         if self.waiting_for_buy == True:

    #             current_candle = data.iloc[1]  # latest candle formed
    #             previous_candle = data.iloc[2]  # last second candle formed

    #             for i in range(1, constant.TRACE_CANDLE + 1):
    #                 current_candle = data.iloc[i]
    #                 previous_candle = data.iloc[i + 1]

    #                 if current_candle[constant.CLOSE] >= previous_candle[constant.HIGH]:
    #                     high_values = [float(data.iloc[j][constant.HIGH]) for j in range(i, 1, -1)]
    #                     try:
    #                         max_high = max(high_values)
    #                     except:
    #                         max_high = current_candle[constant.HIGH]
    #                     self.price = max_high
    #                     self.trading_price = max_high
    #                     self.trade_details["index"] = token
    #                     break

    #                 elif (8 * (float(current_candle[constant.HIGH]) - float(current_candle[constant.HIGH]))) < (
    #                     float(previous_candle[constant.HIGH]) - float(previous_candle[constant.LOW])
    #                 ):
    #                     # No need to reassign current_candle and previous_candle here since it's already done above.
    #                     self.price = current_candle[constant.HIGH]
    #                     self.trading_price = current_candle[constant.HIGH]
    #                     self.trade_details["index"] = token
    #                     break

    #         # buying conditions
    #         if not self.to_buy and token == self.trade_details["index"]:
    #             if ltp > (constant.BUYING_MULTIPLIER * self.price):
    #                 self.to_buy = True
    #                 self.waiting_to_modify = True
    #                 self.waiting_to_modify_or_sell = True

    #                 self.waiting_for_buy = False

    #                 self.price = ltp
    #                 self.trade_details["success"] = True
    #                 self.trade_details["index"] = token

    #                 self.trade_details["datetime"] = datetime.now()

    #                 write_logs(
    #                     "BOUGHT", token, self.price, "NILL", f"LTP > condition matched self.price {self.trading_price}"
    #                 )

    #                 return (Signal.BUY, self.price, index_info)
    #             return (Signal.WAITING_TO_BUY, self.price, index_info)

    #         # # modify stop loss conditions
    #         # elif self.to_buy and not self.to_modify and self.waiting_to_modify and self.trade_details["index"] == token:
    #         #     if ltp > (self.price*1.20):
    #         #         logger.info(f"Modifying the stop-loss, ltp is 20%greater than original price")
    #         #         self.price = ltp
    #         #         # modifying the stop loss
    #         #         return (Signal.MODIFY, self.price, index_info)
    #         #     elif (data.iloc[1]["Low"] * 0.98) > self.stop_loss_price:
    #         #         logger.info(f"Modifying the stoploss price, current-low {data.iloc[1]['Low']} vs stop-loss-price {self.stop_loss_price} ")
    #         #         self.price = self.stop_loss_price
    #         #         # modifying the stop loss
    #         #         return (Signal.MODIFY, self.price, index_info)
    #         #     else:
    #         #         return (Signal.WAITING_TO_MODIFY, self.price, index_info)

    #         # direct selling condition
    #         if not self.waiting_for_buy:
    #             if (
    #                 self.to_buy
    #                 and self.waiting_to_modify_or_sell
    #                 and self.trade_details["index"] == token
    #                 and self.trade_details["success"] == True
    #             ):

    #                 # finding max of three
    #                 stoploss_1 = self.stop_loss_price
    #                 stoploss_2 = data.iloc[1]["Low"] * constant.SL_LOW_MULTIPLIER_1
    #                 stoploss_3 = min([data.iloc[1]["Low"], data.iloc[2]["Low"]]) * constant.SL_LOW_MULTIPLIER_2
    #                 stoploss_condition_1 = round(max([stoploss_1, stoploss_2, stoploss_3]), 2)

    #                 if ltp >= (constant.TRAIL_SL_1 * self.price):
    #                     self.stop_loss_price = max(
    #                         round((self.price * constant.MODITY_STOP_LOSS_1), 2), stoploss_condition_1
    #                     )
    #                     self.price = self.stop_loss_price
    #                     logger.info(f"Modifying the stop-loss 20% condition, New_SL={self.stop_loss_price}")
    #                     return (Signal.MODIFY, self.stop_loss_price, index_info)

    #                 elif ltp >= (constant.TRAIL_SL_2 * self.price):
    #                     self.stop_loss_price = max(
    #                         round((self.price * constant.MODITY_STOP_LOSS_1), 2), stoploss_condition_1
    #                     )
    #                     self.price = self.stop_loss_price
    #                     logger.info(f"Modifying the stop-loss 10% condition, New_SL={self.stop_loss_price}")
    #                     return (Signal.MODIFY, self.stop_loss_price, index_info)

    #                 elif stoploss_condition_1 > self.stop_loss_price:
    #                     self.stop_loss_price = stoploss_condition_1
    #                     self.price = self.stop_loss_price
    #                     logger.info(
    #                         f"Modifying the stop-loss according to Low condition, New_SL={self.stop_loss_price}"
    #                     )
    #                     return (Signal.MODIFY, self.stop_loss_price, index_info)

    #                 elif ltp <= self.stop_loss_price:
    #                     self.trade_details["success"] = False
    #                     self.trade_details["index"] = None
    #                     self.trade_details["datetime"] = datetime.now()

    #                     self.to_buy = False
    #                     self.waiting_to_modify_or_sell = False

    #                     self.to_sell = True
    #                     self.waiting_for_buy = True
    #                     return (Signal.SELL, ltp, index_info)
    #                 else:
    #                     self.waiting_to_modify_or_sell = True
    #                     return (Signal.WAITING_FOR_MODIFY_OR_SELL, self.stop_loss_price, index_info)
    #             else:
    #                 self.waiting_to_modify_or_sell = True
    #                 return (Signal.WAITING_FOR_MODIFY_OR_SELL, self.stop_loss_price, index_info)

    #         elif self.waiting_to_modify_or_sell:
    #             return (Signal.WAITING_FOR_MODIFY_OR_SELL, self.price, index_info)

    #         else:
    #             self.waiting_for_buy = True
    #             self.trade_details["success"] = False
    #             return (Signal.WAITING_TO_BUY, self.price, index_info)
    #     except Exception as exc:
    #         logger.error(f"An error occurred while checking indicators: {exc}")
    #         return (Signal.NULL, 0, [])
