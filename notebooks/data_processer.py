import pandas as pd
import numpy as np
import yfinance as yf
from stockdex import Ticker

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
        self.name = yf.Ticker(symbol).info["shortName"]
        
    def get_key_financials(self):
        return Ticker(self.symbol).macrotrends_key_financial_ratios
    
    def get_earning_dates(self):
        return self.get_key_financials().keys().to_list()
    
    def get_data_key(self):
        key_financials = self.get_key_financials()
        latest_earn_date = key_financials.keys().to_list()[0]
        df = pd.DataFrame(index=[0])
        df["Ticker"] = self.symbol
        df["Name"] = self.name
        df["Date"] = latest_earn_date
        df["3M Future Change"], df["6M Future Change"], df["9M Future Change"], df["1Y Future Change"] = np.nan, np.nan, np.nan, np.nan
        for feature in key_financials.index.to_list():
            df[feature] = key_financials[latest_earn_date][feature]
        return df

# # a must-have
# display(ticker.macrotrends_key_financial_ratios)
# # also very good
# display(ticker.macrotrends_balance_sheet)
# display(ticker.macrotrends_cash_flow)
# display(ticker.macrotrends_income_statement)
# # these are probably harder to include
# display(ticker.macrotrends_ebitda_margin)
# display(ticker.macrotrends_gross_margin)
# display(ticker.macrotrends_net_margin)
# display(ticker.macrotrends_operating_margin)
# display(ticker.macrotrends_pre_tax_margin)