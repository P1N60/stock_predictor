import pandas as pd
import re
import warnings
import io
from bs4 import BeautifulSoup
from .selenium_patch import PatchedSeleniumInterface

class Ticker:
    EXCHANGE_SUFFIX_MAP = {
        ".CO": "cph",  # Copenhagen
        ".OL": "osl",  # Oslo
        ".DE": "etr",  # Xetra
        ".HE": "hel",  # Helsinki
        ".ST": "sto",  # Stockholm
        ".SW": "sto",  # Swiss dual-listed symbols often routed to Stockholm naming on stockanalysis
        ".MI": "bit",  # Borsa Italiana
        ".L": "lon",   # London
        ".PA": "epa",  # Euronext Paris
        ".AS": "ams",  # Euronext Amsterdam
        ".BR": "bru",  # Euronext Brussels
        ".LS": "lis",  # Euronext Lisbon
        ".MC": "bme",  # Bolsa de Madrid
        ".IR": "ise",  # Euronext Dublin
        ".WA": "wse",  # Warsaw
    }

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        self.selenium_interface = None

    def _get_url(self, ticker: str) -> str:
        # Handling different ticker formats for stockanalysis.com
        # Format: https://stockanalysis.com/quote/{exchange}/{ticker}/financials/ratios/
        # Or US: https://stockanalysis.com/stocks/{ticker}/financials/ratios/
        
        base = "https://stockanalysis.com"
        normalized_ticker = ticker.strip().upper()

        for suffix, exchange in self.EXCHANGE_SUFFIX_MAP.items():
            if normalized_ticker.endswith(suffix):
                clean_ticker = normalized_ticker[: -len(suffix)].replace('-', '.')
                return f"{base}/quote/{exchange}/{clean_ticker}/financials/ratios/"

        # Default to US stocks logic
        # If it doesn't have a recognized suffix, assume US (e.g. AAPL)
        us_symbol = normalized_ticker.replace('-', '.')
        return f"{base}/stocks/{us_symbol}/financials/ratios/"

    def key_financial_ratios(self, frequency: str = "annual") -> pd.DataFrame:
        """
        Retrieve the key financial ratios for the given ticker from stockanalysis.com.
        """
        url = self._get_url(self.ticker)
        
        if not hasattr(self, "selenium_interface") or self.selenium_interface is None:
            self.selenium_interface = PatchedSeleniumInterface(use_custom_user_agent=True)
            
        if frequency == "quarterly":
            url += "?p=quarterly"
            # Use the toggling method for quarterly requests to ensure we click the button if URL params are ignored
            soup = self.selenium_interface.get_html_content_with_quarterly_toggle(url)
        else:
            soup = self.selenium_interface.get_html_content(url)
        
        # Validation checks
        soup_str = str(soup)
        if not soup_str or len(soup_str) < 100:
            raise Exception(f"Failed to retrieve valid HTML content for {self.ticker}. URL: {url}. Content length: {len(soup_str) if soup_str else 0}")

        # Use io.StringIO to avoid FutureWarning
        try:
            dfs = pd.read_html(io.StringIO(soup_str))
        except ValueError as e:
            if "No tables found" in str(e):
                 raise Exception(f"No tables found in the page for {self.ticker}. Check if the URL is correct: {url}") from e
            raise e
        except Exception as e:
             raise Exception(f"Error parsing HTML for {self.ticker}: {e}") from e

        if not dfs:
            raise Exception(f"No tables found for {self.ticker}")
        
        # The main ratio table is usually the first one or we can concat them if split
        # Inspecting stockanalysis.com, they often have one main table for ratios
        data = dfs[0]
        
        # The first column is usually the metric name. Set it as index.
        # Check column name, it's often unnamed or dynamic (Date)
        if data.shape[1] > 1:
            data.set_index(data.columns[0], inplace=True)
        
        return data.transpose()
