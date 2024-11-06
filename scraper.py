
import yfinance as yf
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

class Scraper:
    def __init__(self, ticker: str):
        self.ticker = ticker

    def get_stock_info(self) -> str:
        """
        Using yahoo finance to get latest stock price of last day
        based on self.ticker(str): Company ticker
        """
        stock_info = yf.Ticker(self.ticker).history(period="1d")
        if not stock_info.empty:
            date = stock_info.index[0].strftime('%Y-%m-%d')
            open_price = stock_info['Open'].values[0]
            high_price = stock_info['High'].values[0]
            low_price = stock_info['Low'].values[0]
            close_price = stock_info['Close'].values[0]
            volume = stock_info['Volume'].values[0]
            
            return (f"On {date}, the stock price for {self.ticker} opened at ${open_price:.2f}, "
                    f"reached a high of ${high_price:.2f}, a low of ${low_price:.2f}, "
                    f"and closed at ${close_price:.2f}. The trading volume was {volume}.")
        else:
            return f"{self.ticker} possibly delisted; no stock price data found"

    def get_finance_news(self) -> str:
        """
        Scrape latest news headlines from the yahoo finance news
        based on ticker(str): Company Ticker
        """
        # Set up Selenium WebDriver with headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
            #Add these 2 if memory issue faced in hosting in streamlit
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
        chrome_options.add_argument("--disable-software-rasterizer")  # Prevents GPU fallback

        # Set up the WebDriver using webdriver-manager
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.set_page_load_timeout(30)  # Increase page load timeout
        driver.implicitly_wait(10)  # Implicitly wait for elements to be available

        # Set up the URL for the news section of the ticker
        url = f"https://finance.yahoo.com/quote/{self.ticker}/news/"
        # Fetch headlines form the html
        driver.get(url)
        # Create a News string for vectorstore
        news_items = driver.find_elements("css selector", "h3.clamp")
        news = f"Latest News for {self.ticker}:\n"
        for item in news_items:
            title = item.text
            # Get the next sibling element which is the paragraph
            detail = item.find_element("xpath", "following-sibling::p").text
            news += f"{title}: {detail}\n"
        
        driver.quit()

        return news