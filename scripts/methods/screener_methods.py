import pandas as pd
import numpy as np
import yfinance as yf

def get_gettables(symbol: str):
    return display(pd.DataFrame(yf.Ticker(symbol).info.values(), yf.Ticker("AAPL").info.keys()))

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

    # score calculation
    # value score 
    def PE_score(self) -> float:
        if self.PE >= 0:
            score = (-self.PE+self.exp_PE)/self.exp_PE
        else:
            score = -(abs(self.PE))/self.exp_PE*2
        if score < -1:
            return -1
        else:
            return round(score, 2)
        
    def ROA_score(self) -> float:
        score = self.ROA/12
        if score > 1:
            return 1
        elif score < -1:
            return -1
        else:
            return round(score, 2)
    
    # quality score
    def leadership_score(self) -> float:
        score = 0
        people = self.info["companyOfficers"]
        for person in range(len(people)):
            try:
                title = people[person]["title"]
                age = people[person]["age"]
                expected_age = 58.15
                if "CEO" in title:
                    score += (age/expected_age  - 1)*6
                elif "CFO" in title or "CTO" in title:
                    score += (age/expected_age  - 1)*4
                else:
                    score += (age/expected_age  - 1)*1
            except:
                continue
        return round(score/len(people) * 1.5, 2)

    def insider_buy_score(self) -> float:
        return round(self.insider_buy()*0.005, 2)

    # larger scores for final recommendation score 
    def value_score(self) -> float:
        return round((self.PE_score() + self.ROA_score()), 2)
    
    def quality_score(self) -> float:
        return round((self.insider_buy_score() + self.leadership_score()), 2)

    # final score
    def recommendation_score(self) -> float:
        return round(self.value_score() + self.quality_score(), 2)
    
    def recommendation_signal(self) -> str:
        if self.recommendation_score() >= 0.5:
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
            "Value Score": self.value_score(),
            "Quality Score": self.quality_score(),
            "P/E Score": self.PE_score(),
            "ROA Score": self.ROA_score(),
            "Leadership Score": self.leadership_score(),
            "Insider Buy Score": self.insider_buy_score(),
            "P/E": self.PE,
            "ROA%": self.ROA,
            "Insider Buy%": self.insider_buy(),
            "Sector": self.info["sector"],
            "Industry": self.info["industry"],
            "Country": self.info["country"],
            "Owned": self.owned()
            }])
        return df