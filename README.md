# AlpacaBot

A HFT Bot built using Alpaca API. Trading strategy implemented in this project:

1. Calculate rate of change (ROC) of ***ask_price*** of all stocks for last 1 min timeframe from a list (list contains tickers of all stocks you want to watch out for).
2. For the stock with highest ROC (let's call it S_1), compare *ask_price* and *last_traded_price* (LTP) for 1 minute timeframe (if an order is not yet placed using this bot, timeframe for the 1st trade ever will be 30 mins, then 1 min for every trade after 1st trade is placed). 
3. If, for S_1, **ask_price > LTP**, **BUY S_1 with 100% capital allocation**. Else compare ASK and LTP for stock with 2nd highest ROC (S_2), and repeat step 3 till we find a stock with **ASK > LTP** in the ROC sorted list. 
4. Sell after 2% gain.
5. Repeat steps 1-4.

# Steps to building the Alpaca Trading Bot 

1. **Getting started with Alpaca**

  **Create an account with Alpaca**: You can either sign up for a live account or a paper trading account to get started. Navigate to the Alpaca home page – https://alpaca.markets/ and click on Sign up.

 **Get an API Key**: After creating an account, log in to view your API key and secret key. The endpoint used to make calls to the REST API should also be displayed. Take note of all three of these values and save in ***auth.txt*** file as key-value pairs.

 **Install the Alpaca Python Library**: Alpaca has a library, otherwise known as the client SDK, which simplifies connecting to the API. To install it, type in ***pip3 install alpaca-trade-api*** from your command prompt. 
  
  
2. **Connect to Alpaca API using your API Key**
```
  key = json.loads(open('auth.txt', 'r').read())
  api = alpaca.REST(key['APCA-API-KEY-ID'], key['APCA-API-SECRET-KEY'], base_url='https://paper-api.alpaca.markets', api_version = 'v2')
```


3. **Get all stock tickers to moniter from the *Tickers.txt* file** 
```
  tickers = open('Tickers.txt', 'r').read()
  tickers = tickers.upper().split()
```


4. **Get data for all tickers in our list using Alpaca API and save as .csv files for checking our criterias**
  ```
  def get_minute_data(tickers):

      def save_min_data(ticker):
          prices = api.get_trades(str(ticker), start = ((dt.now().astimezone(timezone('America/New_York'))) - timedelta(minutes=2)).isoformat(),
                                          end = ((dt.now().astimezone(timezone('America/New_York')))).isoformat(), 
                                          limit = 10000).df[['price']]
          prices.index = pd.to_datetime(prices.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M')
          prices = prices[~prices.index.duplicated(keep='last')]

          quotes = api.get_quotes(str(ticker), start = ((dt.now().astimezone(timezone('America/New_York'))) - timedelta(minutes=2)).isoformat(),
                                          end = ((dt.now().astimezone(timezone('America/New_York')))).isoformat(), 
                                          limit = 10000).df[['ask_price']]
          quotes.index = pd.to_datetime(quotes.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M')
          quotes = quotes[~quotes.index.duplicated(keep='last')]

          df = pd.merge(prices, quotes, how= 'inner', left_index=True, right_index= True)
          df.to_csv('{}.csv'.format(ticker))

      for ticker in tickers:
          save_min_data(ticker)
```
*NOTE: This function will run periodically to fetch real-time market data for checking criterias.*

*NOTE 2: If bot hasn't placed any trade yet (i.e trading for the first time), it will run a different function (since, for the first time, we won't calculate ROC and compare ASK vs LTP for 1-minute timeframe, but for 30 mins)

*This function will run to fetch data for the first time*

```
 def get_past30_data(tickers):

     def save_30_data(ticker):
         prices_1 = api.get_trades(str(ticker), start = ((dt.now().astimezone(timezone('America/New_York'))) - timedelta(minutes=30)).isoformat(),
                                         end = ((dt.now().astimezone(timezone('America/New_York'))) - timedelta(minutes=28)).isoformat(), 
                                         limit = 10000).df[['price']]
         prices_2 = api.get_trades(str(ticker), start = ((dt.now().astimezone(timezone('America/New_York'))) - timedelta(minutes=2)).isoformat(),
                                         end = ((dt.now().astimezone(timezone('America/New_York')))).isoformat(), 
                                         limit = 10000).df[['price']]

         prices_1.index = pd.to_datetime(prices_1.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M')
         prices_2.index = pd.to_datetime(prices_2.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M')

         prices = pd.concat([prices_1, prices_2])
         prices = prices[~prices.index.duplicated(keep='last')]

         quotes_1 = api.get_quotes(str(ticker), start = ((dt.now().astimezone(timezone('America/New_York'))) - timedelta(minutes=30)).isoformat(),
                                         end = ((dt.now().astimezone(timezone('America/New_York'))) - timedelta(minutes=28)).isoformat(), 
                                         limit = 10000).df[['ask_price']]
         quotes_2 = api.get_quotes(str(ticker), start = ((dt.now().astimezone(timezone('America/New_York'))) - timedelta(minutes=2)).isoformat(),
                                         end = ((dt.now().astimezone(timezone('America/New_York')))).isoformat(), 
                                         limit = 10000).df[['ask_price']]

         quotes_1.index = pd.to_datetime(quotes_1.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M')
         quotes_2.index = pd.to_datetime(quotes_2.index, format = '%Y-%m-%d').strftime('%Y-%m-%d %H:%M')

         quotes = pd.concat([quotes_1, quotes_2])
         quotes = quotes[~quotes.index.duplicated(keep='last')]

         df = pd.merge(prices, quotes, how= 'inner', left_index=True, right_index= True)
         df.to_csv('{}.csv'.format(ticker))

     for ticker in tickers:
         save_30_data(ticker)

```


5. **Following functions calculates ROC for all tickers in our list, compares ASK vs LTP prices, and returns the stock ticker which satisfies all our criterias.**

 ```
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
         df = pd.read_csv('{}.csv'.format(tickers[i]))
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
             max_ROC_index = ROCs.index(max_ROC)

             for i in range(len(tickers)):
                 if(len(tickers)==0):
                     break
                 buy_stock_init = tickers[max_ROC_index]

                 df = pd.read_csv('{}.csv'.format(buy_stock_init))
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
     if os.path.isfile('FirstTrade.csv'):
         timeframe = 1
     else:
         timeframe = 30
     stock = stock_to_buy(tickers, timeframe)
     return stock
```

6. **After we find the ticker which satisfies all the criterias, we place a buy/sell order depending on our market position.**
  
  If our market position is open (i.e we do not hold any stocks in our portfolio), we place a buy order. 
  
  If we hold a position (i.e we have a stock in our portfolio), we check for returns. If returns >= 1%, we sell the current stock and buy the stock that we just found out satisfies all our criterias.
  
 ```
 def buy(stock_to_buy: str):

     cashBalance = api.get_account().cash
     price_stock = api.get_last_trade(str(stock_to_buy)).price
     targetPositionSize = ((float(cashBalance)) / (price_stock)) # Calculates required position size
     api.submit_order(str(stock_to_buy), targetPositionSize, "buy", "market", "day") # Market order to open position    

     mail_content = '''ALERT

     BUY Order Placed for {}: {} Shares at ${}'''.format(stock_to_buy, targetPositionSize, price_stock)

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
     return mail_content

 def sell(current_stock, stock_to_buy):
     # sells current_stock
     quantity = int(api.list_positions()[0].qty)    
     sell_price = api.get_last_trade(str(current_stock)).price
 #     api.submit_order(str(current_stock), quantity, 'sell', 'market', 'day')
     api.close_position(str(current_stock))

     mail_content = '''ALERT

     SELL Order Placed for {}: {} Shares at ${}'''.format(current_stock, quantity, sell_price)

     df = pd.DataFrame()
     df['Time'] = ((dt.now()).astimezone(timezone('America/New_York'))).strftime("%H:%M:%S")
     df['Ticker'] = current_stock
     df['Type'] = 'sell'
     df['Price'] = sell_price
     df['Quantity'] = quantity
     df['Total'] = quantity * sell_price

     with open('Orders.csv', 'a') as f:
         df.to_csv(f, header=f.tell()==0)

     return mail_content

 def check_rets(current_stock, stock_to_buy):
     # checks returns for stock in portfolio (api.get_positions()[0].symbol)
     buy_price = float(api.get_position(current_stock).avg_entry_price) * float(api.get_position(current_stock).qty)
     current_price = float(api.get_position(current_stock).current_price) * float(api.get_position(current_stock).qty)

     if ((current_price - buy_price)/(buy_price))* 100 >=2:
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
```

*NOTE: **mail_alert** function notifies the bot user via mail whenever an order is placed.*

7. **main() function** 
 ```
 def main():

     while True:
         if api.get_clock().is_open == True:

             # check if we have made the first ever trade yet, if yes, timeframe = 1 min, else trade at 10:00 am
             if os.path.isfile('FirstTrade.csv'):
                 get_minute_data(tickers)
                 stock_to_buy = algo(tickers)

                 if len(api.list_positions()) == 0:
                     mail_content = buy(stock_to_buy)
                     mail_alert(mail_content, 5)
                     continue

                 else:
                     current_stock = api.list_positions()[0].symbol
                     mail_content = check_rets(current_stock, stock_to_buy)

                     if mail_content == 0:
                         continue

                     if len(api.list_positions()) == 0:
                         mail_alert(mail_content, 0)    
                         mail_content = buy(stock_to_buy)
                         mail_alert(mail_content, 5)
                         # time.sleep(5)
             else:
                 get_past30_data(tickers)
                 stock_to_buy = algo(tickers)
                 mail_content = buy(stock_to_buy)
                 mail_alert(mail_content, 5)
                 df = pd.DataFrame()
                 df['First Stok'] = stock_to_buy
                 df.to_csv('FirstTrade.csv')
```

 1. Checks if *FirstTrade.csv* exists (i.e if we are using the bot for the first time). Exists if we've made the first trade, else not.
 2. If *FirstTrade.csv* does not exist, we check criterias for first 30 mins when market opens, find **stock_to_buy** using **algo** function, and place a buy order.
 3. If *FirstTrade.csv* exists, bot fetches data for 1-min timeframe, checks for criterias with **algo** function and saves as variable **stock_to_buy**. If we have a open position (*len(api.list_positions()) == 0*), bot places a **buy** order for **stock_to_buy** and sends a buy order mail alert to user. If we do not have an open position, bot checks for returns. If returns >= 2%, bot sells the current stock in portfolio and buys **stock_to_buy**, sends mail alert for sell and buy trades. If return is not >= 2%, bot repeats step 3.
