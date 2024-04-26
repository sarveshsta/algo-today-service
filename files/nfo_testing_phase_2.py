import sched, time
import pandas as pd
from smartapi.smartConnect import SmartConnect
import pandas as pd
import requests
import login as l
import pyotp
from datetime import datetime, date, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler

# variables to be entered

order_symbol='NIFTY'
order_strike=00
call_or_put='CE'
order_qty=10
order_exch_seg='NFO'
order_variety='NORMAL'
order_type='Market'
time_interval='FIVE_MINUTE'
token_info=pd.Series()

# don't disturb these
sell_order_id=0
buy_order_id=0
sell_check_count=0
global Buy
global Sell
global waiting_for_buy
global waiting_for_sell
Buy = True
Sell=False
waiting_for_sell=False
waiting_for_buy=False
bought_price=0
sold_price=0
global cum_profit
cum_profit=0
x=1.012
y=0.988
z=0.968
a=1.032


# -------setup of program------------
obj=SmartConnect(api_key=l.api_key)
data = obj.generateSession(l.user_name,
                            l.password,
                            pyotp.TOTP("").now())  # enter otp

AUTH_TOKEN = data['data']['jwtToken']
refreshToken= data['data']['refreshToken']
FEED_TOKEN=obj.getfeedToken()
res=obj.getProfile(refreshToken)

#fetch the feedtoken
feedToken=obj.getfeedToken()
l.feed_token = feedToken

# --------functions are defined here (don't disturb)
def GetHistoricalAPI():
        to_date= datetime.now()
        # from_date= datetime.now()
        from_date = to_date - timedelta(days=1)

        from_date_format = from_date.strftime("%Y-%m-%d %H:%M")
        to_date_format = to_date.strftime("%Y-%m-%d %H:%M")

        #Historic api
        #enter order_token
        try:
            historicParam={
            "exchange": order_exch_seg,
            "symboltoken": order_token, 
            "interval": time_interval,
            "fromdate": from_date_format, 
            "todate": to_date_format
            }
            candel_json = obj.getCandleData(historicParam)
            return candel_json
        except Exception as e:
            print("Historic Api failed: {}".format(e.message))

def Place_Order(buy_sell,price):
        try:
            orderparams ={
                "variety": order_variety,
                "tradingsymbol": order_symbol,
                "symboltoken": order_token,
                "transactiontype": buy_sell,
                "exchange": order_exch_seg,
                "ordertype": order_type,
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": price,
                "squareoff": "0",
                "stoploss": "0",
                "quantity": order_qty
            }
            orderId=obj.placeOrder(orderparams)
            print("The order id is: {}".format(orderId))
            return orderId
        except Exception as e:
            print("Order placement failed: {}".format(e))

def Modify_Order(buy_sell,price):
        try:
            orderparams ={
                "variety": order_variety,
                "tradingsymbol": order_symbol,
                "symboltoken": order_token,
                "transactiontype": buy_sell,
                "exchange": order_exch_seg,
                "ordertype": order_type,
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": price,
                "squareoff": "0",
                "stoploss": "0",
                "quantity": order_qty
            }
            orderId=obj.modifyOrder(orderparams)
            print("The order id is: {}".format(orderId))
        except Exception as e:
            print("Order modification failed: {}".format(e))

def initializeSymbolTokenMap():
    url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
    # d = requests.get(url).json()

    response = requests.get(url)
    response.raise_for_status()  # raises exception when not a 2xx response
    if response.status_code != 204:
        d = response.json()
        global token_df
        token_df = pd.DataFrame.from_dict(d)
        token_df['expiry'] = pd.to_datetime(token_df['expiry'])
        token_df = token_df.astype({'strike': float})
        l.token_map = token_df
    else:
        print("error")

def getTokenInfo( exch_seg, instrumenttype, symbol, strike_price, pe_ce ) :
    df = l.token_map
    strike_price = strike_price * 100

    if exch_seg == 'NFO' and (instrumenttype == 'OPTSTK' or instrumenttype == 'OPTIDX' ):
        return df[(df['exch_seg'] == 'NFO') & (df['instrumenttype'] == instrumenttype) & (df['name'] == symbol) & (df['strike'] == strike_price) & (df['symbol'].str.endswith(pe_ce)) & (df['expiry']>= str(datetime.today()))].sort_values(by=['expiry'])

def GetCandleData(symbolInfo):
    to_date= datetime.now()
    # from_date= datetime.now()
    from_date = to_date - timedelta(days=1)
   # from_date = to_date - timedelta(days=1
    from_date_format = from_date.strftime("%Y-%m-%d %H:%M")
    to_date_format = to_date.strftime("%Y-%m-%d %H:%M")
    try:
        historicParam={
            "exchange":symbolInfo.exch_seg,
            "symboltoken":symbolInfo.token,
            "interval": "FIVE_MINUTE",
            # "fromdate": 'f{date.today()-datetime.timedelta(90)} 09:15',
            # "todate": 'f{date.today()-datetime.timedelta(1)} 14:00'
            "fromdate": from_date_format,
            "todate": to_date_format
        }
        res_json= obj.getCandleData(historicParam)
        columns= ['timestamp','Open','High','Low','Close','Volume']
        df =pd.DataFrame(res_json['data'], columns=columns)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format = '%Y-%m-%dT%H:%M:%S')
        df['symbol'] = symbolInfo.symbol
        df['expiry'] = symbolInfo.expiry
        # print(f"Done for {symbolInfo.symbol}")
        # print(df)
        return df
    except Exception as e:
        print(f"Historic Api Failed: {e} {symbolInfo.symbol}")
    
def First_Order():
    buy_order_id = Place_Order('BUY',initial_high)
    Buy=False
    Sell=False
    waiting_for_buy=True
    bought_price=initial_high
    return buy_order_id

# def Get_LTP():
    # data = obj.ltpData(order_exch_seg,order_symbol,order_token)
    # ltp=data['data']['ltp']
    # return ltp

def MaxMin_Of_Last_Two_Transactions(symbolinfo):
    df=GetCandleData(symbolinfo)
    # columns= ['timestamp','Open','High','Low','Closing','Volume']
    # df = pd.DataFrame(res_json['data'], columns=columns)
    # df['timestamp'] = pd.to_datetime(df['timestamp'], format= '%Y-%m-%d %H:%M')
    df=df.round(decimals=2)
    # print(df)

    lastthreevalues=df.tail(3)
    # print(lastthreevalues)

    H1=lastthreevalues.iloc[1]['High'] # last value
    H2=lastthreevalues.iloc[0]['High'] # Second last value
    # H3=lastthreevalues.iloc[0]['High']

    L1=lastthreevalues.iloc[1]['Low']
    L2=lastthreevalues.iloc[0]['Low']
    # L3=lastthreevalues.iloc[0]['Low']

    H= max(H1,H2)
    L= min(L1,L2)
    present_H=lastthreevalues.iloc[2]['High']
    present_L=lastthreevalues.iloc[2]['Low']

    return H,L,present_H,present_L,H1,L1

 
# -----------loop function--------------
def Trading(token_info,Buy,Sell,waiting_for_buy,waiting_for_sell,bought_price,sold_price,cum_profit):
    # global Buy
    # global Sell
    # global waiting_for_buy
    # global waiting_for_sell
    # Buy = True
    # Sell=False
    # waiting_for_sell=False
    # waiting_for_buy=False
    print("\n\ninside trading with symbolinfo : ",token_info["symbol"])
    print("buy : ",Buy,"Sell :",Sell,"waiting for buy : ",waiting_for_buy,"waiting for sell : ",waiting_for_sell)
    # we are waiting for buy command to become successful
    new_H,new_L,present_H,present_L=MaxMin_Of_Last_Two_Transactions(token_info)

    if Buy==False and Sell==False and waiting_for_buy==True:
        # tbook=obj.tradeBook()
        # tb_df=pd.DataFrame(tbook['data'])
        # for i in range(len(tb_df)):
        #     if tb_df['orderid'][i] == buy_order_id:
        #         Sell=True
        #         Buy=False
        #         waiting_for_buy=False
        #         print("bought : ",buy_order_id)
        #     break
        print("checking for buy to become true")
        
        if present_H > bought_price:
            print("bought successfully as prsent HIgh : ",present_H," > bought Price ",bought_price)
            Buy=False
            Sell=True
            waiting_for_buy=False

        elif waiting_for_buy==True:
            if new_H != bought_price:
                # mid=Modify_Order(Buy, new_L)
                # buy_order_id=mid
                bought_price=new_H
                print("Order modified---new price : ",bought_price)
        
        else:
            print("no change made in buying cmmnd")


    # we have bought and will now sell 
    elif Buy==False and Sell==True:
        print("Selling for you")
        # max, min = MaxMin_Of_Last_Two_Transactions(token_info)

        # sell_order_id = Place_Order('SELL', min)
        sold_price=new_L
        Buy=False
        Sell=False
        waiting_for_sell= True
        print(" cmmnd given for sell at price :", sold_price)


    # we have given command of sell and waiting for it to become successful 
    elif Buy==False and Sell==False and waiting_for_sell==True:
        # tbook = obj.tradeBook()
        # tb_df=pd.DataFrame(tbook['data'])

        # for i in range(len(tb_df)):
        #     if tb_df['orderid'][i] == sell_order_id:
        #         Sell = False
        #         Buy = True
        #         waiting_for_sell = False
        #         cum_profit = cum_profit + (sold_price - bought_price)
        #         print(" sold : ",sell_order_id )
        #         print(" cum : ", cum_profit)
        print("waiting for sell to become true")
        # new_H,new_L=MaxMin_Of_Last_Two_Transactions(token_info)

        if present_L < sold_price:
            print("sold successfully as new low : ",present_L," < sold Price ",sold_price)
            Buy=True
            Sell=False
            waiting_for_sell=False
            waiting_for_buy=False
            cum_profit = cum_profit + (sold_price - bought_price)
            print( " cum :",cum_profit)


        elif waiting_for_sell==True:
            # new_H,new_L=MaxMin_Of_Last_Two_Transactions()
            if new_L!= sold_price:
                # mid = Modify_Order('SELL',new_L)
                # sell_order_id=mid
                sold_price=new_L
                print("order modified-----new sold price : ", sold_price)
                Buy=False
                Sell=False
                waiting_for_buy=False
        
        else:
            print("no change made in sell")
    # previous was sold and now we will buy a new   
    elif Buy==True and Sell==False:
        print("Buying for you")
        # max, min = MaxMin_Of_Last_Two_Transactions(token_info)

        # buy_order_id = Place_Order('Buy',min)
        Buy = False
        Sell = False
        waiting_for_buy=True
        waiting_for_sell=False
        bought_price=new_H
        print("cmmnd given for bought at price : ",new_H)
        print("buy : ",Buy)
        print("waiting_for_buy : ",waiting_for_buy)
    
    return Buy,Sell,waiting_for_buy,waiting_for_sell,bought_price,sold_price,cum_profit


    

s = sched.scheduler(time.time, time.sleep)
stop_flag = False
cum_profit=0

def run_scheduled_task():
    global Buy,Sell,waiting_for_buy,waiting_for_sell,bought_price,sold_price,cum_profit
    # Get the current time in the format of hh:mm
    current_time = time.strftime('%H:%M')

    # If current time is between 9:15 am and 3:14 pm, execute the function
    if current_time =='16:39':
        initializeSymbolTokenMap()
        token_info = getTokenInfo(order_exch_seg,'OPTIDX',order_symbol,order_strike,call_or_put).iloc[0]
        print(token_info)
        print(token_info['symbol'],"------", token_info['token'],"-----", token_info['lotsize'])
        if not stop_flag:
            # Schedule the next call to this function after 30 seconds
            s.enter(30, 1, run_scheduled_task, ())
            Buy=True
            Sell=waiting_for_buy=waiting_for_sell=False
            bought_price=sold_price=0
            print("program running")

    elif current_time > '09:25' and current_time <= '16:14':
        token_info = getTokenInfo(order_exch_seg,'OPTIDX',order_symbol,order_strike,call_or_put).iloc[0]
        Buy,Sell,waiting_for_buy,waiting_for_sell,bought_price,sold_price,cum_profit= Trading(token_info,Buy,Sell,waiting_for_buy,waiting_for_sell,bought_price,sold_price,cum_profit)
        if not stop_flag:
            # Schedule the next call to this function after 30 seconds
            s.enter(30, 1, run_scheduled_task, ())
            print("program running")
    
    # If current time is past 3:14 pm, set the stop flag to True
    elif current_time > '16:14':
        setattr(stop_flag, 'value', True)
    
    # If current time is before 9:15 am, schedule the next call to this function at 9:15 am
    else:
        next_call_time = time.strptime('09:25', '%H:%M')
        next_call_time = time.mktime(next_call_time)
        s.enterabs(next_call_time, 1, run_scheduled_task, ())
        
# Calculate the time until 9:15 am
now = time.time()
today = time.localtime(now)
next_call_time = time.strptime('16:39', '%H:%M')
next_call_time = time.mktime(today[:3] + next_call_time[3:])

# Schedule the first call to this function at 9:15 am
s.enterabs(next_call_time, 1, run_scheduled_task, ())
# Set a timer to stop the scheduler after 6 hours and 59 minutes (from 9:15 am to 3:14 pm)
s.enter(24540, 1, lambda: setattr(stop_flag, 'value', True), ())
s.run()