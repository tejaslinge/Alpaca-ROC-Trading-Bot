# AlpacaBot

A HFT Bot built using Alpaca API. Trading strategy implemented in this project:

1. Calculate rate of change (ROC) of ***ask_price*** of all stocks from a list (list contains tickers of all stocks you want to watch out for).
2. For the stock with highest ROC (let's call it S_1), compare *ask_price* and *last_traded_price* (LTP) for 1 minute timeframe. 
3. If, for S_1, **ask_price > LTP**, **BUY S_1 with 100% capital allocation**. Else compare ASK and LTP for stock with 2nd highest ROC (S_2), and repeat step 3 till we find a stock with **ASK > LTP** in the ROC sorted list. 
4. Sell after 1% gain.
5. Repeat steps 1-4.

