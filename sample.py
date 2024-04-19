
    def check_indicators(self, data: pd.DataFrame, token:pd.DataFrame,  index: int = 0) -> tuple[Signal, float]:
        current_high = data["High"].iloc[-1]
        last_second_high = data["Open"].iloc[-2]
        # last_third_high = data["Open"].iloc[-3]
        token = str(token).split(':')[-1]
        print("DATA FRAME", data)
        if not self.to_buy:
            if current_high >= (last_second_high + (last_second_high * 0.01)):
                print("CH/CH1/CH2", current_high, last_second_high)
                self.to_buy = True
                self.waiting_for_sell = True

                self.to_sell = False
                self.waiting_for_buy = False
                self.price = current_high
                self.trade_details['done'] = True
                self.trade_details['index'] = token
                self.trade_details['datetime'] = datetime.now()
                print("TRADE BOUGHT", self.trade_details)
                print("Bought Price", self.price)
                return Signal.BUY, self.price
            return Signal.WAITING_TO_BUY, self.price
        
        # condition to sell 
        elif self.to_buy and not self.to_sell and self.waiting_for_sell \
            and self.trade_details['index'] == token:
            print("HIGH/LOW/PRICE", data["High"].iloc[-1], data["Low"].iloc[-1], self.price)
            if ltp_price >= 1.12 * self.price:
                return Signal.WAITING_TO_SELL, self.price
            if (data["High"].iloc[-1] >= self.price * 1.10):
                self.to_sell = True
                self.waiting_for_buy = True

                self.to_buy = False
                self.waiting_for_sell = False
                self.trade_details['datetime'] = datetime.now()
                self.price = data['High'].iloc[-1]
                print("Selling price", self.price)
                print("TRADE SOLD", self.trade_details)
                return Signal.SELL, self.price
            elif (data["Low"].iloc[-1] <= self.price * 0.95):
                
                self.to_sell = True
                self.waiting_for_buy = True

                self.to_buy = False
                self.waiting_for_sell = False
                self.trade_details['datetime'] = datetime.now()
                self.price = data['Low'].iloc[-1]
                print("Selling price", self.price)
                print("TRADE SOLD", self.trade_details)
                return Signal.SELL, self.price
            return Signal.WAITING_TO_SELL, self.price

        elif not self.to_sell and self.to_buy and not self.waiting_for_buy:
            self.waiting_for_sell = True
            print("TRADE DETAILS", self.trade_details)
            return Signal.WAITING_TO_SELL, self.price
        
        else:
            self.waiting_for_buy = True
            self.trade_details['done'] = False
            self.trade_details['index'] = None
            print("TRADE DETAILS", self.trade_details)
            return Signal.WAITING_TO_BUY, self.price
        