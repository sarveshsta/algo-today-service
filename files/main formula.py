import pandas as pd
import matplotlib.pyplot as plt

from smartapi.smartConnect import SmartConnect
import pandas as pd
import requests
import login as l
import pyotp
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler

obj=SmartConnect(api_key=l.api_key)
data = obj.generateSession(l.user_name,
                                l.password,
                                pyotp.TOTP("---").now())  # enter otp 

AUTH_TOKEN = data['data']['jwtToken']
refreshToken= data['data']['refreshToken']
FEED_TOKEN=obj.getfeedToken()
res=obj.getProfile(refreshToken)
# print(res)

#fetch the feedtoken
feedToken=obj.getfeedToken()
l.feed_token = feedToken

def getHistoricalAPI(token, interval ='FIFTEEN_MINUTE'):
        to_date= datetime.now()
        from_date = to_date - timedelta(days=3)

        from_date_format = from_date.strftime("%Y-%m-%d %H:%M")
        to_date_format = to_date.strftime("%Y-%m-%d %H:%M")

        #Historic api
        try:
            historicParam={
            "exchange": "NSE",
            "symboltoken": token,
            "interval": interval,
            "fromdate": from_date_format, 
            "todate": to_date_format
            }
            candel_json = obj.getCandleData(historicParam)
            return candel_json
        except Exception as e:
            print("Historic Api failed: {}".format(e.message))

def place_order(symbol, token, qty, exch_seg, buy_sell,ordertype,price):
        try:
            orderparams ={
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": token,
                "transactiontype": buy_sell,
                "exchange": exch_seg,
                "ordertype": ordertype,
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": price,
                "squareoff": "0",
                "stoploss": "0",
                "quantity": qty
            }
            orderId=obj.placeOrder(orderparams)
            print("The order id is: {}".format(orderId))
        except Exception as e:
            print("Order placement failed: {}".format(e))

def modify_order(symbol, token, qty, exch_seg, buy_sell,ordertype,price):
        try:
            orderparams ={
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": token,
                "transactiontype": buy_sell,
                "exchange": exch_seg,
                "ordertype": ordertype,
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": price,
                "squareoff": "0",
                "stoploss": "0",
                "quantity": qty
            }
            orderId=obj.modifyOrder(orderparams)
            print("The order id is: {}".format(orderId))
        except Exception as e:
            print("Order placement failed: {}".format(e))


res_json =getHistoricalAPI(1594)
columns= ['Date','Open','High','Low','Close','Volume']
df = pd.DataFrame(res_json['data'], columns=columns)
df['Date'] = pd.to_datetime(df['Date'], format= '%Y-%m-%dT%H:%M:%S')
df=df.round(decimals=2)
# df["Date"] = pd.to_numeric(df["Date"])
print(df)

# df=pd.read_csv("D:\\tradedata27Feb\\TATAMOTORS-EQ.csv",index_col=False)
#rint(df)
#print(df["EMA9"])
# print(df["Close"])
listoftimes=df["Date"]

#print(df["Date"]=="21-12-2020 09:35")
#print(df[(df['Date']=='22-12-2020 09:35')]['SMA26'])
# print(df[(df['Date']==' 2023-03-28 10:00:00+05:30 ')]['Close'])
#print(df[(df['Date']=='22-12-2020 09:35')]['EMA9'])

BUY=False
SELL=False
buyorder=0
sellorder=0
firstorder=0
exitime="15:20"
notradetime="15:25"
# print(listoftimes)
stoplossbuy=0
stoplosssell=0
entrytime="2023-03-28 09:30:00+05:30"
entrytime1="2023-03-28 9:15:00+05:30"
entrytime2="2023-03-28 9:20:00+05:30"
entrytime3="2023-03-28 9:25:00+05:30"
#entrytime3="3:25"
longentry=0
shortentry=0
stoplosshit=0
cumprofit=0
count=0
#dfexpo=pd.DataFrame(columns= ['Date','open','high','low','close','order'])
for i in range(len(listoftimes)):
    # if(entrytime in df["Volume"][i]  ):
    # if(entrytime in df["Date"][i]):
    # print(df["Date"][i])
    if i>1:
        lowtemp=[]
        lowtemp.append(df["Low"][i-1])
        lowtemp.append(df["Low"][i-2])
        stoplossbuy=min(lowtemp)

        hightemp = []
        hightemp.append(df["High"][i - 2])
        hightemp.append(df["High"][i-1])
        # hightemp.append(df["High"][i - 2])
        stoplosssell = max(hightemp)
        print( i ," : ",str(stoplossbuy)  + "-----"+str(stoplosssell))

        if(df["High"].values[i]>stoplosssell and BUY==False and buyorder==0):
        # if(df["High"].values[i]>stoplosssell and BUY==False and buyorder==0 and entrytime1 not in df["Date"][i] and entrytime2 not in df["Date"][i] and entrytime3 not in df["Date"][i] and notradetime not in df["Date"][i]):
           print("Order for Buy placed at = ")
           BUY=True
           buyorder = 1
           count+=1
        if (df["Low"].values[i] < stoplossbuy and SELL==False and buyorder==0):
        # if (df["Low"].values[i] < stoplossbuy and SELL==False and buyorder==0 and entrytime1 not in df["Date"][i] and entrytime2 not in df["Date"][i] and entrytime3 not in df["Date"][i] and notradetime not in df["Date"][i]):
           print("Order for Sell placed  at = " )
           SELL=True
           buyorder=1
           count+=1
           '''
        if (exitime in df["Date"][i]):
           if(BUY==True and stoplosshit==0):
                print("Sell at exit time = " + df["Date"][i])
                BUY=False
                buyorder = 0
                cumprofit=cumprofit+df["Close"][i]-stoplosssell
                print("cumprofit " + str(cumprofit))
                stoplosshit = 0
            if (SELL == True and stoplosshit==0):
                print("Buy at exit time = " + df["Date"][i])
                SELL = False
                buyorder = 0
                cumprofit = cumprofit + stoplossbuy-df["Close"][i]
                print("cumprofit " + str(cumprofit))
                stoplosshit = 0
            '''
        if SELL==True and df["High"][i]>stoplosssell and stoplosshit==0:
            print("stop loss hit at ")
            stoplosshit=1
        if BUY==True and df["Low"][i]<stoplossbuy and stoplosshit==0:
            print("stop loss hit at ")
            stoplosshit = 1
        if stoplosshit==1 and BUY == True:
            BUY=False
            buyorder = 0
            stoplosshit = 0
            cumprofit=cumprofit-(stoplosssell-stoplossbuy)
            print("cumprofit "+str(cumprofit))
            print("cumprofit date ")
        if stoplosshit == 1 and SELL == True:
            SELL = False
            buyorder = 0
            stoplosshit = 0
            cumprofit = cumprofit - (stoplosssell-stoplossbuy)
            print("cumprofit " + str(cumprofit))
        

print(round(cumprofit,2))
print(count)
print(round(cumprofit*100/count))
