import pandas as pd
import numpy as np
from methods.scraper import *

def get_raw_data(ticker: str, frequency: str="quarterly") -> pd.DataFrame:
    data = Ticker(ticker).key_financial_ratios(frequency=frequency)
    return data

def imputer(df: pd.DataFrame, max_nans_share: float) -> pd.DataFrame:
    symbol = df.loc[df.index[0], "Ticker"]
    df = df.drop("Ticker", axis=1)
    
    # go through all data points and count nans
    row_nans = [0 for _ in df.index]
    col_nans = [0 for _ in df.columns]
    i = 0
    for row in df.index:
        j = 0
        for column in df.columns:
            val = df.loc[row, column]
            if type(val) == str:
                val = val.replace("%", "") # type: ignore
                val = val.replace("-", "") # type: ignore
            if val == '':
                val = np.nan
                df.loc[row, column] = np.nan
            if np.isnan(float(val)): # type: ignore
                row_nans[i] += 1
                col_nans[j] += 1
            else:
                df.loc[row, column] = float(val) # type: ignore
            j += 1
        i += 1
                
    # delete rows and columns with too many nans or missing price
    drop_rows = []
    for i in range(len(df.index)):
        if row_nans[i]/len(df.columns) > max_nans_share or np.isnan(df.loc[df.index[i], "Close Price"]): # type: ignore
            drop_rows.append(df.index[i])
    drop_cols = []
    for j in range(len(df.columns)):
        if col_nans[j]/len(df.index) > max_nans_share:
            drop_cols.append(df.columns[j])
    df = df.drop(drop_rows)
    df = df.drop(drop_cols, axis=1)

    # impute last nan values
    for j in range(len(df.columns)):
        if df.columns[j] in ["Future Change%"]:
            continue
        impute_indices = []
        for i in range(len(df.index)):
            if np.isnan(df.iloc[i, j]): # type: ignore
                impute_indices = [i]
                u = i-1 if i != 0 else 0
                l = i+1 if i != len(df.index)-1 else len(df.index)-1
                while np.isnan(df.iloc[i, j]): # type: ignore
                    if np.isnan(df.iloc[u, j]) == False and np.isnan(df.iloc[l, j]) == False: # type: ignore
                        for k in impute_indices:
                            df.iloc[k, j] = round((df.iloc[u, j]+df.iloc[l, j])/2, 2) # type: ignore
                    if np.isnan(df.iloc[u, j]) == False and l == len(df.index)-1: # type: ignore
                        for k in impute_indices:
                            df.iloc[k, j] = round(df.iloc[u, j], 2) # type: ignore
                    if u == 0 and np.isnan(df.iloc[l, j]) == False: # type: ignore
                        for k in impute_indices:
                            df.iloc[k, j] = round(df.iloc[l, j], 2) # type: ignore
                    if np.isnan(df.iloc[u, j]): # type: ignore
                        impute_indices.append(u) # type: ignore
                        if u != 0:
                            u += -1 
                    if np.isnan(df.iloc[l, j]): # type: ignore
                        impute_indices.append(l) # type: ignore
                        if l != len(df.index)-1:
                            l += 1

    df.insert(0, "Ticker", symbol)
    return df

def get_data(ticker: str, frequency: str="quarterly") -> pd.DataFrame:
    data = get_raw_data(ticker=ticker, frequency=frequency)

    # get future pice change targets
    earning_prices = []
    for row in data.index:
        earning_prices.append(float(data.loc[row, "Last Close Price"])) # type: ignore
    earning_changes = [np.nan]
    for i in range(1, len(earning_prices)):
        earning_changes.append((earning_prices[i-1]/earning_prices[i]-1)*100)

    data.insert(0, "Future Change%", earning_changes)
    data.insert(0, "Close Price", earning_prices)
    data.insert(0, "Ticker", ticker)
    data = data.drop("Last Close Price", axis=1)

    data = imputer(data, max_nans_share=0.3)

    return data
