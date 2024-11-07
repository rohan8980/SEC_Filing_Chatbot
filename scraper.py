
import yfinance as yf
import requests
from bs4 import BeautifulSoup

class Scraper:
    def __init__(self, ticker: str, company_name: str):
        self.ticker = ticker
        self.company_name = company_name

    def get_stock_info(self) -> str:
        """
        Using yahoo finance to get latest stock price of 5 last days
        based on self.ticker(str): Company ticker
        """
        latest_period = "5d" # Valid periods: ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
        stock_info = yf.Ticker(self.ticker).history(period=latest_period)
        if not stock_info.empty:
            stock_mrkdwn = stock_info.to_markdown() 
            return f"The stock price history of {self.company_name} for last 5 days is:\n {stock_mrkdwn}"
        else:
            return f"{self.company_name} possibly delisted; no stock price data found"
    
    def get_finance_news_gglnews(self) -> str: 
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
    
    def get_finance_news_gglsrch(self) -> str:
        """
        Scrape latest news headlines and details from the google search 50 results
        by searching: ""company_name" finance news" > News tab
        """
        top_n_results = 50
        url = f"https://www.google.com/search?&q=%22{self.company_name.replace(' ','+')}%22+finance+news&tbm=nws&num={top_n_results}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = soup.find_all('h3')

        news = f"Latest News for {self.company_name}:\n"
        for item in news_items:
            title = item.get_text()
            parent_detail = item.find_parent('a')
            # detail = parent_detail.find_next('div').find_next('div').find_next('div').find_next('div').find_next('div').find_next('div').find_next('div')
            detail = parent_detail.find_next('img').find_next('div') 
            detail = ' : ' + detail.get_text() if detail else ""

            news += f"{title}: {detail}\n"

        return news
            