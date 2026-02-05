import stockdex.selenium_interface
import stockdex.macrotrends_interface
import stockdex.justetf_interface
import stockdex.digrin_interface 
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import sys
import pandas as pd
from bs4 import BeautifulSoup
import warnings

print("Patching stockdex selenium interface for aarch64 Linux compatibility...")

class PatchedSeleniumInterface(stockdex.selenium_interface.selenium_interface):
    def __init__(self, use_custom_user_agent: bool = False):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        
        # Point to the system installed chromium only on Linux
        if sys.platform != "win32":
            if os.path.exists("/usr/bin/chromium-browser"):
                self.chrome_options.binary_location = "/usr/bin/chromium-browser"
            elif os.path.exists("/usr/bin/chromium"):
                 self.chrome_options.binary_location = "/usr/bin/chromium"

        if use_custom_user_agent:
            from stockdex.lib import get_user_agent
            self.chrome_options.add_argument(f"user-agent={get_user_agent}")

    def _get_service(self):
        # 1. Check system locations for chromedriver (best for aarch64 Linux)
        if sys.platform != "win32":
            system_driver_paths = [
                "/usr/bin/chromedriver",
                "/usr/local/bin/chromedriver",
                "/usr/lib/chromium-browser/chromedriver",
                "/usr/lib64/chromium-browser/chromedriver",
                "/usr/bin/chromium-driver"
            ]
            for path in system_driver_paths:
                if os.path.exists(path):
                    return Service(executable_path=path)
        
        # 2. Try webdriver-manager on non-Windows (fallback for Linux)
        if sys.platform != "win32":
            try:
                return Service(ChromeDriverManager().install())
            except Exception as e:
                print(f"WebDriverManager failed: {e}")
        
        # 3. If nothing works, let Selenium try to find it (for Linux/PATH)
        return Service()

    def get_html_content(self, url: str) -> str:
        service = self._get_service()
        try:
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
        except Exception as e:
            if "executable needs to be in PATH" in str(e) or "Service" in str(e) or "Unsupported platform" in str(e):
                 raise Exception("Could not find a valid chromedriver. Please run 'sudo dnf install chromedriver' (Fedora) or 'sudo apt install chromium-driver' (Debian/Ubuntu) to install it for aarch64.") from e
            if "SessionNotCreatedException" in str(e) or "session not created" in str(e).lower():
                 print(f"Session creation failed. Service path: {service.path if service.path else 'default'}")
            raise e

        try:
            driver.get(url)
            page_source = driver.page_source
        finally:
            driver.quit()
        
        return BeautifulSoup(page_source, "html.parser")

    def just_etf_get_html_after_click(self, url: str, button_xpath: str):
        service = self._get_service()
        driver = webdriver.Chrome(service=service, options=self.chrome_options)
        try:
            driver.get(url)
            x_path = '//*[@id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]'
            self.click_on_element(x_path, driver)
            self.click_on_element(button_xpath, driver)
            return BeautifulSoup(driver.page_source, "html.parser")
        finally:
            driver.quit()

# Patch logic for finding table data (fixes UnboundLocalError and SyntaxWarning)
def patched_find_table_in_url(self, text_to_look_for: str, soup: BeautifulSoup) -> pd.DataFrame:
    # Fallback: Search all scripts for originalData which contains the table content
    scripts = soup.find_all("script")
    for script in scripts:
        if script.string and "originalData" in script.string:
            original_data = script.string
            for line in original_data.split("\n"):
                if "originalData" in line:
                    try:
                        data = line.split(" = ")[1]
                        if "//" in data: data = data.split("//")[0]
                        data = data.strip().rstrip(";")
                        data = data.replace("null", "None")
                        # Fix invalid escape sequences (like \/) before eval
                        data = data.replace(r"\/", "/")
                        
                        # Suppress SyntaxWarning during eval just in case
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore", SyntaxWarning)
                            return pd.DataFrame(eval(data))
                    except Exception:
                        continue
    
    raise Exception(f"Could not find 'originalData' in page script tags. Looked for text: '{text_to_look_for}'")

# Apply patches
stockdex.selenium_interface.selenium_interface = PatchedSeleniumInterface
stockdex.macrotrends_interface.MacrotrendsInterface._find_table_in_url = patched_find_table_in_url

# Re-apply to modules
stockdex.macrotrends_interface.selenium_interface = PatchedSeleniumInterface
stockdex.justetf_interface.selenium_interface = PatchedSeleniumInterface
if hasattr(stockdex.digrin_interface, 'selenium_interface'):
    stockdex.digrin_interface.selenium_interface = PatchedSeleniumInterface

print("Patch applied: Selenium configured and Parsing logic updated.")