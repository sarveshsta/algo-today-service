import pandas as pd
from smartapi.smartConnect import SmartConnect
import pandas as pd
import requests
import login as l
import pyotp
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
import json

# variables to be entered
order_symbol='NIFTY'
order_strike=00
call_or_put='PE'
order_exch_seg='NFO'
order_variety='NORMAL'
order_type='Market'
time_interval='FIVE_MINUTE'


# don't disturb these
sell_order_id=0
buy_order_id=0
Buy=False
Sell=False
waiting_for_sell=False
waiting_for_buy=False
bought_price=0
sold_price=0
cum_profit=0
count=0
# DOUBLE HIGH MULTIPLIER
x=1.012
#  DOUBLE LOW MULTIPLIER
y=0.988
# SINGLE LOW MULTIPLIER
z=0.70  
# SINGLE HIGH MULTIPLIER
# a=3

# -------setup of program------------
obj=SmartConnect(api_key=l.api_key)
data = obj.generateSession(l.user_name,
                            l.password,
                            pyotp.TOTP("--").now())

AUTH_TOKEN = data['data']['jwtToken']
refreshToken= data['data']['refreshToken']
FEED_TOKEN=obj.getfeedToken()
res=obj.getProfile(refreshToken)

#fetch the feedtoken
feedToken=obj.getfeedToken()
l.feed_token = feedToken

cred={'access_token':obj.access_token,'refresh_token':obj.refresh_token,'feed_token':obj.feed_token,'userId':obj.userId,'api_key':l.api_key}
with open("data.json","w") as jsonfile:
    json.dump(cred, jsonfile)

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
    # to_date= datetime.now()
    to_date = datetime.now() - timedelta(days=0)
    from_date = to_date - timedelta(days=0.5)
    from_date_format = from_date.strftime("%Y-%m-%d %H:%M")
    to_date_format = to_date.strftime("%Y-%m-%d %H:%M")
    try:
        historicParam={
            "exchange":symbolInfo.exch_seg,
            "symboltoken":symbolInfo.token,
            "interval": time_interval,
            "fromdate": from_date_format,
            "todate": to_date_format
            # "fromdate": 'f{date.today()-datetime.timedelta(90)} 09:15',
            # "todate": 'f{date.today()-datetime.timedelta(1)} 14:00'
        }
        res_json= obj.getCandleData(historicParam)
        columns= ['timestamp','Open','High','Low','Close','Volume']
        df =pd.DataFrame(res_json['data'], columns=columns)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format = '%Y-%m-%dT%H:%M:%S')
        df['symbol'] = symbolInfo.symbol
        df['expiry'] = symbolInfo.expiry
        print(f"Done for {symbolInfo.symbol}")
        print(df)
        return df
    except Exception as e:
        print(f"Historic Api Failed: {e} {symbolInfo.symbol}")

def MaxMin_Of_Last_Two_Transactions(symbolinfo):
    res_json=GetCandleData(symbolinfo)
    columns= ['timestamp','Open','High','Low','Closing','Volume']
    df = pd.DataFrame(res_json['data'], columns=columns)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format= '%Y-%m-%d %H:%M')
    # df=df.round(decimals=2)
    # print(df)

    lastthreevalues=df.tail(3)
    # print(lastthreevalues)

    H1=lastthreevalues.iloc[2]['High'] # last value
    H2=lastthreevalues.iloc[1]['High'] # Second last value
    H3=lastthreevalues.iloc[0]['High']

    L1=lastthreevalues.iloc[2]['Low']
    L2=lastthreevalues.iloc[1]['Low']
    L3=lastthreevalues.iloc[0]['Low']

    H= max(H1,H2)
    L= min(L1,L2)
    return H,L

# execution started

initializeSymbolTokenMap()
token_info = getTokenInfo(order_exch_seg,'OPTIDX',order_symbol,order_strike,call_or_put).iloc[0]
print(token_info)
print(token_info['symbol'],"------", token_info['token'],"-----", token_info['lotsize'])

print("candle data")
df = GetCandleData(token_info)
listoftimes=df["timestamp"]

for i in range(len(listoftimes)):
    print("---",i,"---")
    if i==2:
        # buy_order_id = Place_Order('BUY',initial_high)
        # max, min =MaxMin_Of_Last_Two_Transactions(token_info)
        hightemp = []
        hightemp.append(df["High"][i-1])
        hightemp.append(df["High"][i-2])
        max1 = max(hightemp)

        new_H = (max1 * x)

        Buy=False
        Sell=False
        waiting_for_buy=True
        bought_price=new_H
        print("Buy------- First Order price : ", bought_price)

    if i>=2:
    # Trading()
        if Buy==False and Sell==False and waiting_for_buy==True:
            if df["High"][i] > bought_price:
                print("bought successfully at price :", bought_price)
                Buy=False
                Sell=True
                waiting_for_buy=False

            if waiting_for_buy==True:
                # new_H,new_L=MaxMin_Of_Last_Two_Transactions()

                hightemp = []
                hightemp.append(df["High"][i-1])
                hightemp.append(df["High"][i-2])
                max1 = max(hightemp)*x
                # lasthigh = (df["High"][i-1])*a
                # new_H = min(max1,lasthigh)
                new_H =max1


                if new_H != bought_price:
                    # mid=Modify_Order(Buy, new_L)
                    # buy_order_id=mid
                    bought_price=new_H
                    print("Order modified---- New price for buy : ",bought_price)

        elif Buy==False and Sell==True:
            # max, min = MaxMin_Of_Last_Two_Transactions()
            lowtemp = []
            lowtemp.append(df["Low"][i-2])
            lowtemp.append(df["Low"][i-1])
            min1 = [y * min(lowtemp)] 
            singlelow =[]
            singlelow= df["Low"][i-1]
            singlelow1 = singlelow * z
        
            mini = max(singlelow1, min1)
            # mini = min1
            print(" sell at price : ", mini)
            # sell_order_id = Place_Order('SELL', min)
            sold_price=mini
            Buy=False
            Sell=False
            waiting_for_sell= True

        elif Buy==False and Sell==False and waiting_for_sell==True:
            if df["Low"][i] < sold_price:
                print("sold successfully at price : ",sold_price)
                count = count +1
                print("no. of trades completed : ",count)
                Sell = False
                Buy = True
                waiting_for_sell = False
                cum_profit = cum_profit + (sold_price - bought_price)
                lastprofit = (sold_price - bought_price)
                print(" cum : ", cum_profit)
                print("PROFIT IN THIS TRANSACTION :", lastprofit)

            if waiting_for_sell==True:
            # new_H,new_L=MaxMin_Of_Last_Two_Transactions()
                lowtemp = []
                lowtemp.append(df["Low"][i-2])
                lowtemp.append(df["Low"][i-1])
                new_L1 = (min(lowtemp) * y )
                singlelow =[]
                singlelow = df["Low"][i-1]
                singlelow1 = singlelow * z
                # new_L =new_L1
        
                new_L = max(singlelow1, new_L1)
                
                if new_L!= sold_price:
                    sold_price=new_L
                    print("order modified--- new price : ", sold_price)

        elif Buy==True and Sell==False:
            # max, min = MaxMin_Of_Last_Two_Transactions()

            hightemp = []
            hightemp.append(df["High"][i-2])
            hightemp.append(df["High"][i-1])
            new_H1 = max(hightemp)*x
            # lasthigh = (df["High"][i-1])*a
            # new_H = min(lasthigh,new_H1)
            # buy_order_id = Place_Order('Buy',min)
            new_H = new_H1
            print("buy at price : ",new_H)
            Buy = False
            Sell = False
            waiting_for_buy=True
            bought_price=new_H
   


print(" Execution Completed. Great Work ")