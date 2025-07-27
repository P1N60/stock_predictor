import pandas as pd
import numpy as np
import yfinance as yf

def get_gettables():
    return display(pd.DataFrame(yf.Ticker("AAPL").info.keys()))

class Ticker:
    def __init__(self, symbol):
        self.symbol = symbol
        self.info = yf.Ticker(symbol).info
        self.insider = yf.Ticker(symbol).insider_purchases
    
    def name(self) -> str:
        return self.info["shortName"]

    def insider_buy(self) -> float:
        if 'Shares' in self.insider.columns:
            insider_buy = self.insider.loc[self.insider.index[4], "Shares"]
            if pd.isna(insider_buy):
                insider_buy = 0
        return float(insider_buy)
    
    def forward_vs_current_PE(self) -> float:
        try: 
            return self.info["trailingPE"]/self.info["forwardPE"]
        except:
            return 1.00

    def recommendation_old(self) -> float:
        pe = self.info["trailingPE"]
        roa = self.info["returnOnAssets"]*100
        fpe = self.info["forwardPE"]
        return f"{2.6 + np.log(roa+5) - np.log(pe+25) + self.insider_buy()*2:.2f}"

    def recommendation(self) -> float:
        pe = self.info["trailingPE"]
        roa = self.info["returnOnAssets"]*100
        return f"{2.6 + np.log(roa+5) - np.log(pe+25) + self.insider_buy()*2 + np.log(self.forward_vs_current_PE())*0.5:.2f}"

    def summary(self):
        df = pd.DataFrame([{
            "Ticker": self.symbol,
            "Name": self.name(),
            "Recommendation Score": self.recommendation()
        }])
        return df