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
        self.PE = round(self.info["trailingPE"], 2)
        self.ROA = round(self.info["returnOnAssets"]*100, 2)
        self.name = self.info["shortName"]
        self.owned_tickers = pd.read_csv("../data/tickers/owned_tickers.csv")["Ticker"].to_list()
        self.exp_PE = 22
    
    def insider_buy(self) -> float:
        if 'Shares' in self.insider.columns:
            insider_buy = self.insider.loc[self.insider.index[4], "Shares"]*100
            if pd.isna(insider_buy) or insider_buy > 50 or insider_buy < -50:
                insider_buy = 0
        return round(float(insider_buy), 2)

    def owned(self) -> bool:
        if self.symbol in self.owned_tickers:
            return True
        else:
            return False

    def CEO(self) -> dict:
        people = self.info["companyOfficers"]
        for i in range(len(people)):
            if "CEO" in people[i]["title"]:
                return {"name": people[i]["name"], "age": people[i]["age"]}
        return {"name": np.nan, "age": np.nan}

    def PE_score(self) -> float:
        if self.PE >= 0:
            score = (-self.PE+self.exp_PE)/self.exp_PE
        else:
            score = -(abs(self.PE))/self.exp_PE*2
        if score < -1:
            return -1
        else:
            return score
        
    def ROA_score(self) -> float:
        score = self.ROA/12
        if score > 1:
            return 1
        elif score < -1:
            return -1
        else:
            return score
        
    def CEO_age_score(self) -> float:
        ceo_age = self.CEO()["age"]
        if np.isnan(ceo_age):
            return 0
        else:
            return (ceo_age/55 - 1) * 0.4

    def recommendation_score(self) -> float:
        return round((self.PE_score() + self.ROA_score() + self.insider_buy()*0.005 + self.CEO_age_score()) * 2, 2)
    
    def recommendation_signal(self) -> str:
        if self.recommendation_score() >= 1:
            return "Buy"
        elif self.recommendation_score() < 0:
            return "Sell"
        else:
            return "Hold"
        
    def summary(self) -> pd.DataFrame:
        df = pd.DataFrame([{
            "Ticker": self.symbol,
            "Name": self.name,
            "Signal": self.recommendation_signal(),
            "Recommendation Score": self.recommendation_score(),
            "Owned": self.owned(),
            "P/E": self.PE,
            "ROA%": self.ROA,
            "CEO Age": self.CEO()["age"],
            "Insider Buy%": self.insider_buy(),
            "Sector": self.info["sector"],
            "Industry": self.info["industry"],
            "CEO Name": self.CEO()["name"]
            }])
        return df