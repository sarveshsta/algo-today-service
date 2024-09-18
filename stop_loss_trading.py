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

                    if signal == Signal.BUY:
                        self.indicator.price = self.indicator.price
                        self.indicator.stop_loss_price = self.indicator.price * constant.STOP_LOSS_MULTIPLIER
                        logger.info(
                            f"Trade BOUGHT at {self.indicator.price} in {index_info[0]} with SL={self.indicator.stop_loss_price}"
                        )
                        
                        if self.parameters_amount[index] == 0:
                            self.trading_quantity = self.parameters[index]
                            
                        else:
                            for instrument in self.instruments:
                                if instrument.symbol == index:
                                    self.lotsize = int(instrument.lotsize)
                                    self.token_id = instrument.token

                            amount = self.parameters_amount[index]
                            number_of_stocks = int(amount / (self.indicator.price * self.lotsize))
                            quantity = self.lotsize * number_of_stocks
                            self.trading_quantity = quantity
                            logger.info(f"Trade Quantity for {index} - {quantity}")
                           
                        current_time = datetime.now()

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
