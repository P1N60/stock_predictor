import pandas as pd
import re
import warnings
from bs4 import BeautifulSoup
from .selenium_patch import PatchedSeleniumInterface

class Ticker:
    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        self.selenium_interface = None

    def macrotrends_key_financial_ratios(self, frequency: str = "annual") -> pd.DataFrame:
        """
        Retrieve the key financial ratios for the given ticker.
        """
        # Using the ticker twice in the URL usually triggers a redirect to the standard URL with the company name
        url = f"https://www.macrotrends.net/stocks/charts/{self.ticker}/{self.ticker}/financial-ratios"
        
        # build selenium interface object if not already built
        if not hasattr(self, "selenium_interface") or self.selenium_interface is None:
            self.selenium_interface = PatchedSeleniumInterface()

        soup = self.selenium_interface.get_html_content(url)

        if frequency == "quarterly":
            # The initial redirect often strips query parameters or defaults to annual.
            # We must find the canonical URL of the landed page and append the frequency parameter.
            canonical = soup.find("link", {"rel": "canonical"}) # type: ignore
            target_url = None
            
            if canonical and canonical.get("href"): # type: ignore
                target_url = canonical["href"] # type: ignore
            else:
                og_url = soup.find("meta", property="og:url") # type: ignore
                if og_url and og_url.get("content"):
                     target_url = og_url["content"]
            
            if target_url:
                if "?" in target_url:
                    target_url += "&freq=Q"
                else:
                    target_url += "?freq=Q"
                soup = self.selenium_interface.get_html_content(target_url)

        data = self._find_table_in_url("Current Ratio", soup) # type: ignore

        # Clean field names
        if "field_name" in data.columns:
            data["field_name"] = data["field_name"].apply(
                lambda x: re.search(">(.*)<", x).group(1) if re.search(">(.*)<", x) else x # type: ignore
            )
            data = data.set_index("field_name")
            
        if "popup_icon" in data.columns:
            data.drop(columns=["popup_icon"], inplace=True)

        return data.transpose()

    def _find_table_in_url(self, text_to_look_for: str, soup: BeautifulSoup) -> pd.DataFrame:
        """
        Finds the table data in the page scripts (since Macrotrends loads data via JS).
        """
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string and "originalData" in script.string:
                original_data = script.string
                for line in original_data.split("\n"):
                    if "originalData" in line:
                        try:
                            # Extract the array/dict string
                            data_str = line.split(" = ")[1]
                            
                            # Clean up the string to be eval-safe(r)
                            if "//" in data_str: 
                                data_str = data_str.split("//")[0]
                            data_str = data_str.strip().rstrip(";")
                            data_str = data_str.replace("null", "None")
                            data_str = data_str.replace(r"\/", "/")
                            
                            # Parse data
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore", SyntaxWarning)
                                return pd.DataFrame(eval(data_str))
                        except Exception:
                            continue
        
        raise Exception(f"Could not find 'originalData' in page script tags for {self.ticker}")
