import pandas as pd
import numpy as np
import yfinance as yf

def get_gettables():
    return display(pd.DataFrame(yf.Ticker("AAPL").info.values(), yf.Ticker("AAPL").info.keys()))

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
        self.info = yf.Ticker(symbol).info
        self.insider = yf.Ticker(symbol).insider_purchases
        self.pe = round(self.info["trailingPE"], 2)
        self.roa = round(self.info["returnOnAssets"]*100, 2)
        self.name = self.info["shortName"]
        self.expt_pe = 20
        self.expt_roa = 3.25
        self.owned_tickers = pd.read_csv("../data/tickers/owned_tickers.csv")["Ticker"].to_list()
    
    def insider_buy(self) -> float:
        if 'Shares' in self.insider.columns:
            insider_buy = self.insider.loc[self.insider.index[4], "Shares"]*100
            if pd.isna(insider_buy) or insider_buy > 50 or insider_buy < -50:
                insider_buy = 0
        return round(float(insider_buy), 2)

    def forward_PE(self) -> float:
        try: 
            return round(self.info["forwardPE"], 2)
        except:
            return np.nan

    def forward_vs_current_PE(self) -> float:
        try: 
            cvf = round(self.pe/self.info["forwardPE"], 2)
            if cvf > 2 or cvf < 0.5:
                return 1.00
            return cvf
        except:
            return 1.00

    def recommendation_score(self) -> float:
        if self.pe+self.expt_pe  <= 0 or self.roa+self.expt_roa <= 0 or self.forward_PE() <= 0:
            return np.nan
        return round(2 + np.log(self.roa+self.expt_roa) - np.log(self.pe+self.expt_pe) + self.insider_buy()*0.005 + np.log(self.forward_vs_current_PE())/10, 2)
    
    def recommendation_signal(self) -> str:
        if self.recommendation_score() >= 0.75:
            return "Buy"
        elif self.recommendation_score() < 0:
            return "Sell"
        else:
            return "Hold"
        
    def owned(self) -> bool:
        if self.symbol in self.owned_tickers:
            return True
        else:
            return False

    def summary(self) -> pd.DataFrame:
        df = pd.DataFrame([{
            "Ticker": self.symbol,
            "Name": self.name,
            "Signal": self.recommendation_signal(),
            "Recommendation Score": self.recommendation_score(),
            "Owned": self.owned(),
            "Forward P/E": self.forward_PE(),
            "P/E": self.pe,
            "FvC Ratio": self.forward_vs_current_PE(),
            "ROA%": self.roa,
            "Insider Buy%": self.insider_buy(),
            "Sector": self.info["sector"],
            "Industry": self.info["industry"],
            }])
        return df