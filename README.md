# AlpacaBot

A HFT Bot built using Alpaca API. Trading strategy implemented in this project:

1. Calculate rate of change (ROC) of ***ask_price*** of all stocks for last 1 min timeframe from a list (list contains tickers of all stocks you want to watch out for).
2. For the stock with highest ROC (let's call it S_1), compare *ask_price* and *last_traded_price* (LTP) for 1 minute timeframe (if an order is not yet placed using this bot, timeframe for the 1st trade ever will be 30 mins, then 1 min for every trade after 1st trade is placed). 
3. If, for S_1, **ask_price > LTP**, **BUY S_1 with 100% capital allocation**. Else compare ASK and LTP for stock with 2nd highest ROC (S_2), and repeat step 3 till we find a stock with **ASK > LTP** in the ROC sorted list. 
4. Sell after 1% gain.
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

5. 
