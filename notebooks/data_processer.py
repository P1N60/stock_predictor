import pandas as pd
from stockdex import Ticker

class Stock:
    def __init__(self, symbol):
        if symbol:
            self.symbol = symbol
        else:
            print("Please pass a symbol")
        
    def get_key_financials(self):
        return Ticker(self.symbol).macrotrends_key_financial_ratios
    

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