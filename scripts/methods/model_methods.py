import pandas as pd
import numpy as np
import yfinance as yf

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol

    def get_row(self):
        earn_dates = yf.Ticker(self.symbol).earnings.keys().to_list()
        yf_info = yf.Ticker(self.symbol).info
        df = pd.DataFrame()
        for earn_date in earn_dates:
            row_df = pd.DataFrame([{"Ticker": self.symbol}])
            row_df["Name"] = yf_info["shortName"]
            row_df["Date"] = earn_date
            row_df["Sector"] = yf_info["sector"]
            row_df["Industry"] = yf_info["industry"] 
            if earn_date == earn_dates[0]:
                row_df["3M Future Change"], row_df["6M Future Change"], row_df["9M Future Change"], row_df["1Y Future Change"] = np.nan, np.nan, np.nan, np.nan
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
                        got_price = True
                    except:
                        day_offset += -1
                if got_price == True:
                    future_change_cols = ['3M Future Change', '6M Future Change', '9M Future Change', '1Y Future Change']
                    if row_df[future_change_cols].isna().any().any():
                        continue
                else:
                    continue
            for feature in key_financials.index.to_list():
                row_df[feature] = key_financials[earn_date][feature]
                if row_df.loc[0, feature] == "":
                    row_df.loc[0, feature] = np.nan
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