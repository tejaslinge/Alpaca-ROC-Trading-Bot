import pandas as pd
import datetime
from datetime import datetime as dt
from pytz import timezone
import time

import alpaca_trade_api as alpaca
import json

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from datetime import timedelta
import os.path

key = json.loads(open('/home/Bilal/alpacaBOT/AUTH/auth.txt', 'r').read())
api = alpaca.REST(key['APCA-API-KEY-ID'], key['APCA-API-SECRET-KEY'], base_url='https://api.alpaca.markets', api_version = 'v2')
tickers = open('/home/Bilal/alpacaBOT/AUTH/Tickers.txt', 'r').read()
tickers = tickers.upper().split()
global TICKERS 
TICKERS = tickers

def get_minute_data(tickers):
    
    def save_min_data(ticker):
        prices = api.get_trades(str(ticker), start = ((dt.now().astimezone(timezone('America/New_York'))) - timedelta(minutes=2)).isoformat(),
                                        end = ((dt.now().astimezone(timezone('America/New_York')))).isoformat(), 
                                        limit = 10000).df[['price']]
        prices.index = pd.to_datetime(prices.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M')
        prices = prices[~prices.index.duplicated(keep='first')]

        quotes = api.get_quotes(str(ticker), start = ((dt.now().astimezone(timezone('America/New_York'))) - timedelta(minutes=2)).isoformat(),
                                        end = ((dt.now().astimezone(timezone('America/New_York')))).isoformat(), 
                                        limit = 10000).df[['ask_price']]
        quotes.index = pd.to_datetime(quotes.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M')
        quotes = quotes[~quotes.index.duplicated(keep='first')]

        df = pd.merge(prices, quotes, how= 'inner', left_index=True, right_index= True)
        df.to_csv('/home/Bilal/alpacaBOT/tick_data/{}.csv'.format(ticker))
        
    for ticker in tickers:
        save_min_data(ticker)

def get_past30_data(tickers):
    
    def save_30_data(ticker):
        prices_1 = api.get_trades(str(ticker), start = dt.now().astimezone(timezone('America/New_York')).replace(hour=9, minute=30, second = 10).isoformat(),
                                        end = dt.now().astimezone(timezone('America/New_York')).replace(hour=9, minute=32, second = 0).isoformat(), 
                                        limit = 10000).df[['price']]
        prices_2 = api.get_trades(str(ticker), start = dt.now().astimezone(timezone('America/New_York')).replace(hour=9, minute=59, second = 0).isoformat(),
                                        end = dt.now().astimezone(timezone('America/New_York')).replace(hour=10, minute=0, second = 15).isoformat(), 
                                        limit = 10000).df[['price']]
        
        prices_1.index = pd.to_datetime(prices_1.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M')
        prices_2.index = pd.to_datetime(prices_2.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M')
        
        prices = pd.concat([prices_1, prices_2])
        prices = prices[~prices.index.duplicated(keep='first')]

        quotes_1 = api.get_quotes(str(ticker), start = dt.now().astimezone(timezone('America/New_York')).replace(hour=9, minute=30, second = 10).isoformat(),
                                        end = dt.now().astimezone(timezone('America/New_York')).replace(hour=9, minute=32, second = 10).isoformat(), 
                                        limit = 10000).df[['ask_price']]
        quotes_2 = api.get_quotes(str(ticker), start = dt.now().astimezone(timezone('America/New_York')).replace(hour=9, minute=59, second = 0).isoformat(),
                                        end = dt.now().astimezone(timezone('America/New_York')).replace(hour=10, minute=0, second = 15).isoformat(), 
                                        limit = 10000).df[['ask_price']]
        
        quotes_1.index = pd.to_datetime(quotes_1.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M')
        quotes_2.index = pd.to_datetime(quotes_2.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M')
        
        quotes = pd.concat([quotes_1, quotes_2])
        quotes = quotes[~quotes.index.duplicated(keep='first')]
        
        df = pd.merge(prices, quotes, how= 'inner', left_index=True, right_index= True)
        df.to_csv('/home/Bilal/alpacaBOT/tick_data/{}.csv'.format(ticker))
    
    for ticker in tickers:
        save_30_data(ticker)

def ROC(ask, timeframe):
        roc = []
        if timeframe == 30:
            rocs = (ask[ask.shape[0] - 1] - ask[0])/(ask[0])
        else:
            rocs = (ask[ask.shape[0] - 1] - ask[ask.shape[0] -2])/(ask[ask.shape[0] - 2])
        roc.append(rocs)
        return rocs

# Returns a list of most recent ROCs for all tickers
def return_ROC_list(tickers, timeframe):
    ROC_tickers = []
    for i in range(len(tickers)):
        df = pd.read_csv('/home/Bilal/alpacaBOT/tick_data/{}.csv'.format(tickers[i]))
        df.set_index('timestamp', inplace= True)
        df.index = pd.to_datetime(df.index, format ='%Y-%m-%d').strftime('%Y-%m-%d %H:%M')
        ROC_tickers.append(ROC(df['ask_price'], timeframe)) # [-1] forlast value (latest)
    return ROC_tickers

# compared ASK vs LTP
def compare_ask_ltp(tickers, timeframe):
    
        if len(tickers) != 0:
            buy_stock = ''
            ROCs = return_ROC_list(tickers, timeframe)
            max_ROC = max(ROCs)
            
            if max_ROC <= 0:
                return 0
            else: pass
            max_ROC_index = ROCs.index(max_ROC)

            for i in range(len(tickers)):
                if(len(tickers)==0):
                    break
                buy_stock_init = tickers[max_ROC_index]

                df = pd.read_csv('/home/Bilal/alpacaBOT/tick_data/{}.csv'.format(buy_stock_init))
                df.set_index('timestamp', inplace= True)
                df.index = pd.to_datetime(df.index, format ='%Y-%m-%d').strftime('%Y-%m-%d %H:%M')

                # list to keep track of number of ask_prices > price
                buy_condition = []
                ask_col = df.columns.get_loc('ask_price')
                price_col = df.columns.get_loc('price')
                for i in range(df.shape[0] - 2, df.shape[0]):
                    buy_condition.append(df.iloc[i, ask_col] > df.iloc[i,price_col])

                if buy_condition[-1] == True:
                    buy_stock = buy_stock_init
                    return buy_stock
                else:
                    tickers.pop(max_ROC_index)
                    ROCs.pop(max_ROC_index)
                    if(len(tickers)==0):
                        break
                    max_ROC = max(ROCs)
                    max_ROC_index =  ROCs.index(max_ROC)
        else: tickers = TICKERS

# returns which stock to buy
def stock_to_buy(tickers, timeframe):
        entry_buy = compare_ask_ltp(tickers, timeframe)
        return entry_buy

def algo(tickers):

    # Calculates ROC
    # Checks for stock with highest ROC and if ask_price > price
    # Returns ticker to buy
    if os.path.isfile('/home/Bilal/alpacaBOT/FirstTrade.csv'):
        timeframe = 1
    else:
        timeframe = 30
    stock = stock_to_buy(tickers, timeframe)
    return stock


def buy(stock_to_buy: str):
    
    cashBalance = api.get_account().cash
    price_stock = api.get_last_trade(str(stock_to_buy)).price
    targetPositionSize = ((float(cashBalance)) / (price_stock)) # Calculates required position size
    api.submit_order(str(stock_to_buy), targetPositionSize, "buy", "market", "day") # Market order to open position    
    
    mail_content = '''ALERT
    
    BUY Order Placed for {}: {} Shares at ${}'''.format(stock_to_buy, targetPositionSize, price_stock)
    
    if os.path.isfile('/home/Bilal/alpacaBOT/Orders.csv'):
        df = pd.read_csv('/home/Bilal/alpacaBOT/Orders.csv')
        df.drop(columns= 'Unnamed: 0', inplace = True)
        df.loc[len(df.index)] = [((dt.now()).astimezone(timezone('America/New_York'))).strftime("%H:%M:%S"), stock_to_buy, 'buy',
                                 price_stock, targetPositionSize, targetPositionSize*price_stock, api.get_account().cash] 
    else:    
        df = pd.DataFrame()
        df[['Time', 'Ticker', 'Type', 'Price', 'Quantity', 'Total', 'Acc Balance']] = ''
        df.loc[len(df.index)] = [((dt.now()).astimezone(timezone('America/New_York'))).strftime("%H:%M:%S"), stock_to_buy, 'buy',
                                 price_stock, targetPositionSize, targetPositionSize*price_stock, api.get_account().cash] 
    df.to_csv('/home/Bilal/alpacaBOT/Orders.csv')
    return mail_content

def sell(current_stock, stock_to_buy):
    # sells current_stock
    quantity = float(api.list_positions()[0].qty)    
    sell_price = api.get_last_trade(str(current_stock)).price
#     api.submit_order(str(current_stock), quantity, 'sell', 'market', 'day')
    api.cancel_all_orders() # cancels all pending (to be filled) orders 
    api.close_position(str(current_stock)) # sells current stock
    
    mail_content = '''ALERT

    SELL Order Placed for {}: {} Shares at ${}'''.format(current_stock, quantity, sell_price)
    
    df = pd.read_csv('/home/Bilal/alpacaBOT/Orders.csv')
    df.drop(columns= 'Unnamed: 0', inplace = True)
    df.loc[len(df.index)] = [((dt.now()).astimezone(timezone('America/New_York'))).strftime("%H:%M:%S"), current_stock, 'sell',
                             sell_price, quantity, quantity*sell_price, api.get_account().cash] 
    
#     with open('Orders.csv', 'a') as f:
#         df.to_csv(f, header=f.tell()==0)
    df.to_csv('/home/Bilal/alpacaBOT/Orders.csv')
    return mail_content

def check_rets(current_stock, stock_to_buy):
    # checks returns for stock in portfolio (api.get_positions()[0].symbol)
    buy_price = float(api.get_position(current_stock).avg_entry_price) * float(api.get_position(current_stock).qty)
    current_price = float(api.get_position(current_stock).current_price) * float(api.get_position(current_stock).qty)
    
#     if (((current_price - buy_price)/(buy_price))* 100 >= 0.01) or (((current_price - buy_price)/(buy_price))* 100 <= -0.01):
    if ((current_price - buy_price)/(buy_price))* 100 >= 2:
        mail_content = sell(current_stock, stock_to_buy)
    else: 
        mail_content = 0              
    return mail_content

def mail_alert(mail_content, sleep_time):
    # The mail addresses and password
    sender_address = 'sender_address@email.com'
    sender_pass = 'sender_password'
    receiver_address = 'receiver_address@email.com'

    # Setup MIME
    message = MIMEMultipart()
    message['From'] = 'Trading Bot'
    message['To'] = receiver_address
    message['Subject'] = 'HFT Second-Bot'
    
    # The body and the attachments for the mail
    message.attach(MIMEText(mail_content, 'plain'))

    # Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
    session.starttls()  # enable security

    # login with mail_id and password
    session.login(sender_address, sender_pass)
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
    time.sleep(sleep_time)

def main():
    mail_start = 0    
    while True:
        try:
            if api.get_clock().is_open == True:
                # sends mail when bot starts running
                if mail_start == 0:
                    mail_content = 'The bot started running on {} at {}'.format(dt.now().strftime('%Y-%m-%d'), dt.now().strftime('%H:%M:%S'))
                    mail_alert(mail_content, 0)
                    mail_start += 1
                else: pass
                
                # check if we have made the first ever trade yet, if yes, timeframe = 1 min, else trade at 10:00 am
                if os.path.isfile('/home/Bilal/alpacaBOT/FirstTrade.csv'):
                    get_minute_data(tickers)
                    stock_to_buy = algo(tickers)

                    if len(api.list_positions()) == 0:
                        try:
                            if api.get_activities()[0].order_status == 'partially_filled':
                                api.cancel_all_orders()
                        except:
                            pass
                        if stock_to_buy == 0:
                            continue
                        else: pass
                        mail_content = buy(stock_to_buy)
                        mail_alert(mail_content, 5)
                        continue

                    else:
                        current_stock = api.list_positions()[0].symbol
                        mail_content = check_rets(current_stock, stock_to_buy)
                        if mail_content == 0:
                            continue
                        else:
                            mail_alert(mail_content, 0)    
    #                         api.close_all_positions()
    #                         sell(current_stock, stock_to_buy)
    
                            if stock_to_buy == 0:
                                continue
                            else: pass
                    
                            mail_content = buy(stock_to_buy)
                            mail_alert(mail_content, 5)
                            # time.sleep(5)
                else:
                    if ((dt.now().astimezone(timezone('America/New_York')))).strftime('%H:%M:%S') < '10:00:00':
                        time_to_10 = int(str(dt.strptime('10:00:00', '%H:%M:%S') - dt.strptime(((dt.now().astimezone(timezone('America/New_York')))).strftime('%H:%M:%S'), '%H:%M:%S')).split(':')[1])*60 + int(str(dt.strptime('10:00:00', '%H:%M:%S') - dt.strptime(((dt.now().astimezone(timezone('America/New_York')))).strftime('%H:%M:%S'), '%H:%M:%S')).split(':')[2])
                        time.sleep(time_to_10 - 20)

                    get_past30_data(tickers)
                    stock_to_buy = algo(tickers)
                    
                    if stock_to_buy == 0:
                        continue
                    else:
                        pass
                    
                    mail_content = buy(stock_to_buy)
                    mail_alert(mail_content, 5)
                    df = pd.DataFrame()
                    df['First Stock'] = stock_to_buy
                    df.to_csv('/home/Bilal/alpacaBOT/FirstTrade.csv')
            else:
                time.sleep(300)
                if api.get_clock().is_open == True:
                    continue
                else:
                    mail_content = 'The market is closed on {}'.format(dt.now().strftime('%Y-%m-%d'))
                    mail_alert(mail_content, 0)
                    break
        except:
            continue
            
if __name__ == '__main__':
    main()
