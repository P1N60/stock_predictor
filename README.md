# Stock Price Prediction Model

## Instructions
### In the 'notebooks' folder you will find two notebooks: 'screener.ipynd' and 'stock_predictor.ipynb'. The screener is a simple scraper that gets some basic up-to-date financials for a few stocks. This data is saved to '/data/simple_screener_results.csv'

### The main file is the 'stock_predictor', which when run, creates a dataset of the 5-year earnings history of over 1500 stocks. The ticker of theese stocks can be found in '/data/filtered_tickers.csv'. The dataset is then saved to '/data/earnings_data.csv'. In this dataset you will find that the latest datapoints don't have a y-label. Theese rows would be the wanted rows for a prediction today. The rest of the data is used for training and testing. After testing, the metrics will be logged to '/data/test_results.csv'.
