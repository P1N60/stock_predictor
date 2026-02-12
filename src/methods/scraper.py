import pandas as pd
import re
import warnings
import io
from bs4 import BeautifulSoup
from .selenium_patch import PatchedSeleniumInterface

class Ticker:
    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        self.selenium_interface = None

    def _get_url(self, ticker: str) -> str:
        # Handling different ticker formats for stockanalysis.com
        # Format: https://stockanalysis.com/quote/{exchange}/{ticker}/financials/ratios/
        # Or US: https://stockanalysis.com/stocks/{ticker}/financials/ratios/
        
        base = "https://stockanalysis.com"
        
        if ticker.endswith('.CO'):
            clean_ticker = ticker[:-3].replace('-', '.')
            return f"{base}/quote/cph/{clean_ticker}/financials/ratios/"
        elif ticker.endswith('.OL'):
            clean_ticker = ticker[:-3].replace('-', '.')
            return f"{base}/quote/osl/{clean_ticker}/financials/ratios/"
        elif ticker.endswith('.DE'):
            # Xetra
            clean_ticker = ticker[:-3].replace('-', '.')
            return f"{base}/quote/etr/{clean_ticker}/financials/ratios/"
        elif ticker.endswith('.HE'):
            # Helsinki
            clean_ticker = ticker[:-3].replace('-', '.')
            return f"{base}/quote/hel/{clean_ticker}/financials/ratios/"
        elif ticker.endswith('.ST'):
            # Stockholm
            clean_ticker = ticker[:-3].replace('-', '.')
            return f"{base}/quote/sto/{clean_ticker}/financials/ratios/"
            
        # Default to US stocks logic
        # If it doesn't have a recognized suffix, assume US (e.g. AAPL)
        return f"{base}/stocks/{ticker}/financials/ratios/"

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
