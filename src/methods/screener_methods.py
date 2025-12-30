import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from gender_guesser.detector import Detector

def get_gettables(symbol: str):
    return display(pd.DataFrame(yf.Ticker(symbol).info.values(), yf.Ticker("AAPL").info.keys()))

_detector = Detector()
def g_detector(name: str) -> int:
    n = name.split()[1] if len(name.split()) > 1 else ""
    dict = {"female": 1, "mostly_female": 0.5, "unknown": 0, "mostly_male": -0.5, "male": -1}
    return dict[_detector.get_gender(n)]

def mult_if_positive(x: float, y: float) -> float:
    if x > 0:
        return x * y
    elif x < 0:
        return x / y
    else:
        return 0

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
        self.info = yf.Ticker(symbol).info
        self.insider = yf.Ticker(symbol).insider_purchases
        self.PE = self.info["trailingPE"]
        self.ROA = self.info["returnOnAssets"]*100
        self.EPS = self.info["epsTrailingTwelveMonths"]
        self.PB = self.info["priceToBook"]
        self.name = self.info["shortName"]
        self.owned_tickers = pd.read_csv("../data/tickers/owned_tickers.csv")["Ticker"].to_list()
        self.exp_PE = 22

    def price_history(self, range="ytd"):
        price = yf.download(self.symbol, period=range, rounding=False, progress=False, auto_adjust=True)[('Close', self.symbol)]
        return price
    
    def price_graph(self, range="ytd"):
        price = self.price_history(range)
        plt.figure(figsize=[14, 6])
        plt.title(f"{self.symbol} ({self.name}) {range} price history")
        plt.grid(True, alpha=0.6)
        plt.plot(price)
        plt.xticks(price.index[np.linspace(0, len(price) - 1, 10, dtype=int)])
        plt.show()
    
    def insider_buy(self) -> float:
        if 'Shares' in self.insider.columns:
            insider_buy = self.insider.loc[self.insider.index[4], "Shares"]*100
            if pd.isna(insider_buy) or insider_buy > 50 or insider_buy < -50:
                insider_buy = 0
        return float(insider_buy)

    def owned(self) -> bool:
        if self.symbol in self.owned_tickers:
            return True
        else:
            return False

    # score calculation
    # value score 
    def PE_score(self) -> float:
        median = 18.7 # chosen from data by median
        spread = median
        weight = 1.2

        score = -np.tanh((self.PE-median)/(spread/2))*weight # 1 at mean-spread and -1 at mean+spread
        if self.PE >= 0:
            return score 
        else:
            return -score
        
    def ROA_score(self) -> float:
        median = 4.325 # chosen from data by median
        spread = median
        weight = 1.0
        return np.tanh((self.ROA-median)/(spread/2))*weight # -1 at mean-spread and 1 at mean+spread

    def EPS_score(self) -> float:
        median = 4 # chosen from data by median
        spread = median
        weight = 0.0
        return np.tanh((self.EPS-median)/(spread/2))*weight # -1 at mean-spread and 1 at mean+spread

    def PB_score(self) -> float:
        median = 1.875 # chosen from data by median
        spread = 2
        weight = 0.2
        return -np.tanh((self.PB-median)/(spread/2))*weight # 1 at mean-spread and -1 at mean+spread

    # quality score
    def leadership_score(self) -> float:
        mean = 57.15 # chosen from data by median
        spread = 20
        weight = 1.2

        score = 0
        people = self.info["companyOfficers"]
        for person in range(len(people)):
            person_score = 0
            try:
                age = people[person]["age"]
                person_score += np.tanh((age-mean)/(spread/2))
            except:
                Exception
            try:
                name = people[person]["name"]
                person_score += -g_detector(name)
            except:
                Exception
            try:
                title = people[person]["title"]
                if "CEO" in title:
                    person_score = person_score*5
                elif "CFO" in title or "CTO" in title:
                    person_score = person_score*3
                else:
                    person_score = person_score*1
            except:
                Exception
            score += person_score
        score = score/len(people)
        return np.tanh(score/(10/2)) * weight

    def insider_buy_score(self) -> float:
        return self.insider_buy()*0.005

    # larger scores for final recommendation score 
    def value_score(self) -> float:
        return self.PE_score() + self.ROA_score() + self.EPS_score() + self.PB_score()
    
    def quality_score(self) -> float:
        return self.insider_buy_score() + self.leadership_score()

    # final score
    def recommendation_score(self) -> float:
        return self.value_score() + self.quality_score()
    
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
            "Recommendation Score": round(self.recommendation_score(), 2),
            "Value Score": round(self.value_score(), 2),
            "Quality Score": round(self.quality_score(), 2),
            "P/E Score": round(self.PE_score(), 2),
            "ROA Score": round(self.ROA_score(), 2),
            "PB Score": round(self.PB_score(), 2),
            "Leadership Score": round(self.leadership_score(), 2),
            "Insider Buy Score": round(self.insider_buy_score(), 2),
            "P/E": round(self.PE, 2),
            "ROA%": round(self.ROA, 2),
            "Earnings pr. Share": round(self.EPS, 2),
            "Price to Book": round(self.PB, 2),
            "Insider Buy%": round(self.insider_buy(), 2),
            "Sector": self.info["sector"],
            "Industry": self.info["industry"],
            "Country": self.info["country"],
            "Owned": self.owned()
            }])
        return df