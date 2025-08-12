import pandas as pd
import numpy as np
import yfinance as yf
from sklearn.neural_network import MLPRegressor
import numpy as np

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol

    def get_annual_financials(self) -> pd.DataFrame:
        annual_financials = yf.Ticker(self.symbol).get_financials(freq="yearly")
        if annual_financials.shape[1] > 4:
            annual_financials = annual_financials.iloc[:, :4]
        return annual_financials
    
    def get_quarterly_financials(self) -> pd.DataFrame:
        quarterly_financials = yf.Ticker(self.symbol).get_financials(freq="quarterly")
        overlapping_dates = set(self.get_annual_financials().columns).intersection(set(quarterly_financials.columns))
        if overlapping_dates:
            quarterly_financials = quarterly_financials.drop(columns=list(overlapping_dates))
            quarterly_financials = quarterly_financials.iloc[:, :4]
        return quarterly_financials
    
    def get_financials(self) -> pd.DataFrame:
        financials = pd.concat([self.get_annual_financials(), self.get_quarterly_financials()], axis=1).loc[:, ~pd.concat([self.get_annual_financials(), self.get_quarterly_financials()], axis=1).columns.duplicated()]
        try:
            sorted_columns = sorted(financials.columns, key=pd.to_datetime, reverse=True)
            financials = financials[sorted_columns]
        except:
            pass
        if financials.shape[1] > 8:
            financials = financials.iloc[:, :8]
        return financials

    def get_row(self):
        financials = self.get_financials()
        yf_info = yf.Ticker(self.symbol).info
        df = pd.DataFrame()
        earn_dates = financials.columns.to_list()
        for earn_date in earn_dates:
            row_df = pd.DataFrame([{"Ticker": self.symbol}])
            row_df["Name"] = yf_info["shortName"]
            row_df["Date"] = pd.to_datetime(earn_date)
            row_df["Sector"] = yf_info["sector"]
            row_df["Industry"] = yf_info["industry"] 
            if earn_date == earn_dates[0]:
                row_df["3M Future Change"] = np.nan
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
                    if row_df["3M Future Change"].isna().any().any():
                        continue
                else:
                    continue
            for feature in financials.index.to_list():
                row_df[feature] = financials[earn_date][feature]
                if row_df.loc[0, feature] == "":
                    row_df.loc[0, feature] = np.nan
            df = pd.concat([df, row_df])
        return df

class MLPWrapper:
    def __init__(self, hidden_layer_amount=999, neuron_amount=999, **kwargs):
        self.hidden_layer_amount = hidden_layer_amount
        self.neuron_amount = neuron_amount
        self.kwargs = kwargs
        self.iter_no_change = round(2+1000/(np.sqrt(self.neuron_amount*self.hidden_layer_amount)))
        
    def fit(self, X, y):
        # Create tuple of hidden layer sizes
        hidden_layers = tuple([self.neuron_amount] * self.hidden_layer_amount)
        print(f"Trying: {self.hidden_layer_amount} layers, {self.neuron_amount} neurons per layer, iter_no_change={self.iter_no_change}")
        print(f"Hidden layer sizes: {hidden_layers}")
        self.model = MLPRegressor(
            hidden_layer_sizes=hidden_layers,
            learning_rate="adaptive",
            early_stopping=True,
            verbose=False,
            n_iter_no_change=self.iter_no_change,
            **self.kwargs
        )
        result = self.model.fit(X, y)
        print(f"Training completed. Iterations: {self.model.n_iter_}, Final score: {self.model.score(X, y):.4f} \n {"=" * 65}")
        return result
    
    def predict(self, X):
        return self.model.predict(X)
    
    def score(self, X, y):
        return self.model.score(X, y)
    
    def get_params(self, deep=True):
        params = {'hidden_layer_amount': self.hidden_layer_amount, 
                'neuron_amount': self.neuron_amount}
        params.update(self.kwargs)
        return params
    
    def set_params(self, **params):
        for key, value in params.items():
            setattr(self, key, value)
        return self