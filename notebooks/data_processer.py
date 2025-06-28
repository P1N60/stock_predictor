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
        earn_dates = key_financials.keys().to_list()
        df = pd.DataFrame()
        for earn_date in earn_dates:
            row_df = pd.DataFrame(index=[0])
            row_df["Ticker"] = self.symbol
            row_df["Name"] = self.name
            row_df["Date"] = earn_date
            if earn_date == earn_dates[0]:
                row_df["3M Future Change"], df["6M Future Change"], df["9M Future Change"], df["1Y Future Change"] = np.nan, np.nan, np.nan, np.nan
            else:
                price_data = yf.download(self.symbol, period="max", rounding=False, progress=False)
                got_price = False
                day_offset = 0
                while(got_price==False and day_offset > -6):
                    try:           
                        row_df['3M Future Change'] = (
                        price_data.loc[pd.Timestamp(earn_date) + pd.Timedelta(days=day_offset, weeks=13), ('Close', self.symbol)] / 
                        price_data.loc[pd.Timestamp(earn_date) + pd.Timedelta(days=day_offset), ('Close', self.symbol)] - 1
                        )
                        row_df['6M Future Change'] = (
                            price_data.loc[pd.Timestamp(earn_date) + pd.Timedelta(days=day_offset, weeks=26), ('Close', self.symbol)] / 
                            price_data.loc[pd.Timestamp(earn_date) + pd.Timedelta(days=day_offset), ('Close', self.symbol)] - 1
                        )
                        row_df['9M Future Change'] = (
                            price_data.loc[pd.Timestamp(earn_date) + pd.Timedelta(days=day_offset, weeks=39), ('Close', self.symbol)] / 
                            price_data.loc[pd.Timestamp(earn_date) + pd.Timedelta(days=day_offset), ('Close', self.symbol)] - 1
                        )
                        row_df['1Y Future Change'] = (
                            price_data.loc[pd.Timestamp(earn_date) + pd.Timedelta(days=day_offset, weeks=52), ('Close', self.symbol)] / 
                            price_data.loc[pd.Timestamp(earn_date) + pd.Timedelta(days=day_offset), ('Close', self.symbol)] - 1
                        )
                        got_price = True
                    except:
                        day_offset += -1
                if pd.isna(row_df['3M Future Change']) or pd.isna(row_df['3M Future Change']) or pd.isna(row_df['3M Future Change']) or pd.isna(row_df['3M Future Change']):
                    continue
            for feature in key_financials.index.to_list():
                row_df[feature] = key_financials[earn_date][feature]
            df = pd.concat([df, row_df])
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