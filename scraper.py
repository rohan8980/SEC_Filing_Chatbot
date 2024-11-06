
import yfinance as yf
import requests
from bs4 import BeautifulSoup

class Scraper:
    def __init__(self, ticker: str, company_name: str):
        self.ticker = ticker
        self.company_name = company_name

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
        Scrape latest news headlines from the google news
        based on "company_name finance"
        """
        url = f"https://news.google.com/search?q={self.company_name.replace(' ','+')}+finance"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = soup.find_all('a', class_='JtKRv')

        news = f"Latest News for {self.company_name}:\n"
        for item in news_items:
            title = item.get_text()
            href = item.get('href')  # Extract the URL from the 'href' attribute
            full_url = f"https://news.google.com{href}"  # Construct the full URL
            news += f"{title}\n"
            
        return news