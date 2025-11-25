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
        self.PE = round(self.info["trailingPE"], 2)
        self.ROA = round(self.info["returnOnAssets"]*100, 2)
        self.EPS = round(self.info["epsTrailingTwelveMonths"], 2)
        self.PB = round(self.info["priceToBook"], 2)
        self.name = self.info["shortName"]
        self.owned_tickers = pd.read_csv("../data/tickers/owned_tickers.csv")["Ticker"].to_list()
        self.exp_PE = 22

    def price_history(self, range):
        price = yf.download(self.symbol, period=range, rounding=False, progress=False)[('Close', self.symbol)]
        return price
    
    def price_graph(self, range):
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
        return round(float(insider_buy), 2)

    def owned(self) -> bool:
        if self.symbol in self.owned_tickers:
            return True
        else:
            return False

    # score calculation
    # value score 
    def PE_score(self) -> float:
        mean = 18.7 # chosen from data by median
        spread = mean
        weight = 1.15

        score = round(-np.tanh((self.PE-mean)/(spread/2))*weight, 2) # 1 at mean-spread and -1 at mean+spread
        if self.PE >= 0:
            return score 
        else:
            return -score
        
    def ROA_score(self) -> float:
        mean = 4.325 # chosen from data by median
        spread = mean
        weight = 1.15
        return round(np.tanh((self.ROA-mean)/(spread/2))*weight, 2) # -1 at mean-spread and 1 at mean+spread

    def EPS_score(self) -> float:
        mean = 4 # chosen from data by median
        spread = mean
        weight = 0.0
        return round(np.tanh((self.EPS-mean)/(spread/2))*weight, 2) # -1 at mean-spread and 1 at mean+spread

    def PB_score(self) -> float:
        mean = 1.875 # chosen from data by median
        spread = 2
        weight = 0.2
        return round(-np.tanh((self.PB-mean)/(spread/2))*weight, 2) # 1 at mean-spread and -1 at mean+spread

    # quality score
    def leadership_score(self) -> float:
        mean = 57.15 # chosen from data by median
        spread = 20
        weight = 1.1

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
        return round(np.tanh(score/(10/2)) * weight, 2)

    def insider_buy_score(self) -> float:
        return round(self.insider_buy()*0.005, 2)

    # larger scores for final recommendation score 
    def value_score(self) -> float:
        return round((self.PE_score() + self.ROA_score()) + self.EPS_score() + self.PB_score(), 2)
    
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
            "PB Score": self.PB_score(),
            "Leadership Score": self.leadership_score(),
            "Insider Buy Score": self.insider_buy_score(),
            "P/E": self.PE,
            "ROA%": self.ROA,
            "Earnings pr. Share": self.EPS,
            "Price to Book": self.PB,
            "Insider Buy%": self.insider_buy(),
            "Sector": self.info["sector"],
            "Industry": self.info["industry"],
            "Country": self.info["country"],
            "Owned": self.owned()
            }])
        return df