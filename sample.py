
    # def check_indicators(self, data: pd.DataFrame, token:str,  index: int = 0) -> tuple[Signal, float]:
    #     ltp_price = float(data['LTP'][0])
    #     token = token.split(':')[-1]
    #     print("TOKEN", token)

    #     if self.trade_details['index'] == None or self.waiting_for_buy:
    #         if number_of_candles > len(data): number_of_candles= len(data)
    #         for i in range(number_of_candles, 0, -1):
    #         # for i in range(len(data)-1, 0, -1):
    #             current_candle = data.iloc[i]
    #             previous_candle = data.iloc[i - 1]
    #             print(f'C{i} => {current_candle[OHLC_1]} H{i-1} => {previous_candle[OHLC_2]}')
    #             if current_candle[OHLC_1] >= previous_candle[OHLC_2]:
    #                 self.price = current_candle[OHLC_2]
    #                 self.trade_details['index'] = token
    #                 self.trade_details['price'] = self.price
    #                 print("Condition matched", self.price)
    #                 break

    #     current_high = data["High"].iloc[-1]
    #     if not self.to_buy and token == self.trade_details['index']:
    #         if self.price >= current_high * 1.01:
    #             self.to_buy = True
    #             self.waiting_for_sell = True

    #             self.to_sell = False
    #             self.waiting_for_buy = False
    #             self.price = current_high
    #             self.trade_details['done'] = True
    #             self.trade_details['index'] = str(token)
    #             self.trade_details['datetime'] = datetime.now()
    #             self.trade_details = {"done": False, "index": None, 'datetime': datetime.now()}
    #             print("TRADE BOUGHT in", self.trade_details)
    #             return Signal.BUY, self.price
    #         return Signal.WAITING_TO_BUY, self.price
        
    #     elif self.to_buy and not self.to_sell and self.waiting_for_sell \
    #         and self.trade_details['index'] == token:

    #         if ltp_price >= 1.12 * self.price:
    #             print("TRADE DETAILS", self.trade_details)
    #             return Signal.WAITING_TO_SELL, self.price
            
    #         elif ltp_price < self.price * 1.10:
    #             self.to_sell = True
    #             self.waiting_for_buy = True

    #             self.to_buy = False
    #             self.waiting_for_sell = False
    #             self.price = ltp_price
    #             self.trade_details['datetime'] = datetime.now()
    #             self.trade_details['index'] = None
    #             self.trade_details['price'] = self.price
    #             print("LTP PRICE and Selling price", ltp_price, self.price)
    #             print("TRADE SOLD", self.trade_details)
    #             return Signal.SELL, self.price
            
    #         if (data["High"].iloc[-1] >= self.price * 1.10):
    #             self.to_sell = True
    #             self.waiting_for_buy = True

    #             self.to_buy = False
    #             self.waiting_for_sell = False
    #             self.price = data['High'].iloc[-1]
    #             self.trade_details['price'] = self.price
    #             self.trade_details['datetime'] = datetime.now()
    #             self.trade_details['index'] = None
    #             print("TRADE SOLD", self.trade_details)
    #             return Signal.SELL, self.price 
    #         elif (data["Low"].iloc[-1] <= self.price * 0.95):
                
    #             self.to_sell = True
    #             self.waiting_for_buy = True

    #             self.to_buy = False
    #             self.waiting_for_sell = False
    #             self.price = data['Low'].iloc[-1]
    #             self.trade_details['price'] = self.price
    #             self.trade_details['datetime'] = datetime.now()
    #             self.trade_details['index'] = None
    #             print("Selling price", self.price)
    #             print("TRADE SOLD", self.trade_details)
    #             return Signal.SELL, self.price
    #         return Signal.WAITING_TO_SELL, self.price
        
    #     elif not self.to_sell and self.to_buy and not self.waiting_for_buy:
    #         self.waiting_for_sell = True
    #         print("TRADE DETAILS", self.trade_details)
    #         return Signal.WAITING_TO_SELL, self.price
        
    #     else:
    #         self.waiting_for_buy = True
    #         self.trade_details['done'] = False
    #         self.trade_details['index'] = None
    #         print("TRADE DETAILS", self.trade_details)
    #         return Signal.WAITING_TO_BUY, self.price

  