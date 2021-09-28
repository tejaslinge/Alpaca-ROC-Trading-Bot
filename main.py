import numpy as np
import pandas as pd
import datetime
from datetime import datetime as dt
from pytz import timezone
import time

import alpaca_trade_api as alpaca
import json

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from datetime import timedelta
from pandas import ExcelWriter

key = json.loads(open('auth.txt', 'r').read())
api = alpaca.REST(key['APCA-API-KEY-ID'], key['APCA-API-SECRET-KEY'], base_url='https://paper-api.alpaca.markets')

tickers = open('Tickers.txt', 'r').read()
tickers = tickers.upper().split()
# capital = int(open('Capital.txt', 'r').read().replace(" ", ""))

def get_data(tickers: list, timeframe= '1Min'):
    '''
    Saves Close Data For all tickers in .csv files
    tickers: list of tickers from Tickers.txt file
    timeframe: '1Min' (Refer documentation for more)
    '''
    df = pd.DataFrame()

    def quotes_prices(ticker):
        
        # get ask price
        quotes = api.get_quotes(str(ticker), start = (((dt.now()).astimezone(timezone('America/New_York'))) - timedelta(minutes=30)).
                                isoformat(), end = ((dt.now()).astimezone(timezone('America/New_York'))).
                                isoformat(),limit= 10000).df
        quotes.index = pd.to_datetime(quotes.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M') 
        quotes = quotes[~quotes.index.duplicated(keep='last')]
        quotes = quotes[['ask_price']]

        # get last traded price
        prices = api.get_barset(ticker, '1Min', limit = 1000).df
        prices.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        prices = prices[['Close']]
        prices.index = pd.to_datetime(prices.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M')
                
        # get df -> cols: [close, ask_price] and save to csv
        df = pd.merge(prices, quotes, how= 'inner', left_index=True, right_index= True)
        df.to_csv('{}.csv'.format(ticker))
        
    for ticker in (tickers):
        quotes_prices(ticker)
        
def algo(tickers):

    # Calculates ROC
    def ROC(ask, timeframe):
        roc = []
        x = timeframe

        while x < len(ask):
            rocs = (ask[x] - ask[x - timeframe])/(ask[x- timeframe])
            roc.append(rocs)
            x += 1
        return roc

    # Returns a list of most recent ROCs for all tickers
    def return_ROC_list(tickers, timeframe):

        ROC_tickers = []

        for i in range(len(tickers)):
            df = pd.read_csv('{}.csv'.format(tickers[i]))
            df.set_index('Unnamed: 0', inplace= True)
            df.index = pd.to_datetime(df.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M')
            ROC_tickers.append((ROC(df['ask_price'], timeframe)[-1])) # [-1] for last value (latest)
        return ROC_tickers

    # Checks for stock with highest ROC and if ask_price > price 
    # Returns ticker to buy
    
    def stock_to_buy(tickers, timeframe):
        
        def compare_ask_ltp(tickers, timeframe):
            
            buy_stock = ''
            ROCs = return_ROC_list(tickers, timeframe)
            max_ROC_index = ROCs.index(max(ROCs))            
            
            for i in range(len(tickers)):    
                buy_stock_init = tickers[max_ROC_index]

                df = pd.read_csv('{}.csv'.format(buy_stock_init))
                df.set_index('Unnamed: 0', inplace= True)
                df.index = pd.to_datetime(df.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M')
    
                # list to keep track of number of ask_prices > price
                buy_condition = []
                ask_col = df.columns.get_loc('ask_price')
                price_col = df.columns.get_loc('Close')
                for i in range(df.shape[0] - 2, df.shape[0]):
                    buy_condition.append(df.iloc[i, ask_col] > df.iloc[i, price_col])

                if buy_condition[-1] == True:
                    buy_stock = buy_stock_init
                    break
                else:
                    tickers.pop(max_ROC_index)
                    ROCs.pop(max_ROC_index)
                    max_ROC_index =  ROCs.index(max(ROCs))
            return buy_stock
        
        entry_buy = compare_ask_ltp(tickers, timeframe)
        return entry_buy
    
    if (dt.now().astimezone(timezone('America/New_York')).strftime("%H:%M:%S") >= '9:30:00') &
        (dt.now().astimezone(timezone('America/New_York')).strftime("%H:%M:%S") < '10:00:00'):
        timeframe = 30
        
    elif (dt.now().astimezone(timezone('America/New_York')).strftime("%H:%M:%S") >= '10:00:00') &
        (dt.now().astimezone(timezone('America/New_York')).strftime("%H:%M:%S") < '16:00:00'):
        timeframe = 1
        
    else: timeframe = 0
    
    if timeframe != 0:
        stock = stock_to_buy(tickers, timeframe)
    return stock

def buy(stock_to_buy: str):

    cashBalance = api.get_account().cash
    price_stock = api.get_last_trade(str(stock_to_buy)).price
    targetPositionSize = round((float(cashBalance)) / (price_stock)) # Calculates required position size
    api.submit_order(str(stock_to_buy), targetPositionSize, "buy", "market", "gtc") # Market order to open position    
    
    df = pd.DataFrame()
    df['Time'] = ((dt.now()).astimezone(timezone('America/New_York'))).strftime("%H:%M:%S")
    df['Ticker'] = stock_to_buy
    df['Type'] = 'buy'
    df['Price'] = price_stock
    df['Quantity'] = targetPositionSize
    df['Total'] = targetPositionSize * price_stock
    # df['Balance'] = api.get_account().cash
    
    with open('Orders.csv', 'a') as f:
        df.to_csv(f, header=f.tell()==0)

def sell(current_stock, stock_to_buy):
    # sells current_stock
    quantity = int(api.list_positions()[0].qty)    
    sell_price = api.get_last_trade(str(current_stock)).price
    api.submit_order(str(current_stock), quantity, 'sell', 'market', 'fok')
    
    df = pd.DataFrame()
    df['Time'] = ((dt.now()).astimezone(timezone('America/New_York'))).strftime("%H:%M:%S")
    df['Ticker'] = current_stock
    df['Type'] = 'sell'
    df['Price'] = sell_price
    df['Quantity'] = quantity
    df['Total'] = quantity * sell_price
    
    with open('Orders.csv', 'a') as f:
        df.to_csv(f, header=f.tell()==0)

    time.sleep(10)
    buy(stock_to_buy)

def check_rets(current_stock, stock_to_buy):
    # checks returns for stock in portfolio (api.get_positions()[0].symbol)
    buy_price = float(api.get_position(current_stock).avg_entry_price) * int(api.get_position(current_stock).qty)
    current_price = float(api.get_position(current_stock).current_price) * int(api.get_position(current_stock).qty)
    
    if ((current_price - buy_price)/(buy_price))* 100 >= 1:
        sell(current_stock, stock_to_buy)
    else: pass

def check_book():
    get_data(tickers)
    stock_to_buy =  algo(tickers)
    
    if len(api.list_positions()) != 0:
        current_stock = api.list_positions()[0].symbol
    
    openPosition = len(api.list_positions())    
    if openPosition == 0:
        buy(stock_to_buy)
    else:
        check_rets(current_stock, stock_to_buy)        

def main():
    while True:
        if api.get_clock().is_open == False:
            break
        else: check_book()

if __name__ == '__main__':
    main()