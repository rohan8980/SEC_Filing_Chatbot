import requests

class FetchFilings:
    def __init__(self, headers:dict):
        """
        headers (dict): headers for request to api
        """
        self.headers = headers

    def get_companies_cik(self) -> dict:
        """
        Get list of company and its cik 
        Reference: "https://www.sec.gov/files/company_tickers.json"
    
        Returns:
            (dict): dictionary of {name (ticker): cik} 
                'Apple Inc. (AAPL)': '0000320193'
        """
        headers = self.headers
        company_tickers_url = "https://www.sec.gov/files/company_tickers.json"
        company_tickers = requests.get(url = company_tickers_url, headers=headers)
        company_tickers = company_tickers.json()
        company_tickers = {f"{val['title']} ({val['ticker']})": str(val['cik_str']).zfill(10) for val in company_tickers.values()}

        return company_tickers

    def get_sections_10K(self):
        """
        Get dictionary of all sections of 10-K
        """
        return {'1': 'Business',
                '1A': 'Risk Factors',
                '1B': 'Unresolved Staff Comments',
                '1C': 'Cybersecurity',
                '2': 'Properties',
                '3': 'Legal Proceedings',
                '4': 'Mine Safety Disclosures',
                '5': 'Market for Registrant Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities',
                '6': 'Selected Financial Data',
                '7': 'Management’s Discussion and Analysis of Financial Condition and Results of Operations',
                '7A': 'Quantitative and Qualitative Disclosures about Market Risk',
                '8': 'Financial Statements and Supplementary Data',
                '9': 'Changes in and Disagreements with Accountants on Accounting and Financial Disclosure',
                '9A': 'Controls and Procedures',
                '9B': 'Other Information',
                '10': 'Directors, Executive Officers and Corporate Governance',
                '11': 'Executive Compensation',
                '12': 'Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters',
                '13': 'Certain Relationships and Related Transactions, and Director Independence',
                '14': 'Principal Accountant Fees and Services',}

    def get_recent_filings_10K(self, cik: str, count: int=2, ):
        """
        Get SEC filings for a company by CIK (Central Index Key) from EDGAR for last 2 filings
        API Reference: https://sec-api.io/docs/sec-filings-item-extraction-api
        Args:
            cik (str): Central Index Key (CIK) of the company.
            
            count (int): N most recent 10-K filings for the company
        Returns:
            list[dict]: List of recent filings' url and date
        """
        # API URL
        base_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        headers = self.headers
        response = requests.get(url=base_url, headers=headers)
        form_filter = '10-K'

        # Check and return successful response
        if response.status_code == 200:
            data = response.json()
            
            # URL for 10K files
            filings = data['filings']['recent']
            form_filings = [
                {
                    "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accesion_no.replace('-','')}/{primary_document}",
                    "date": filing_date,
                }
                for form, accesion_no, primary_document, filing_date in zip(filings['form'], filings['accessionNumber'], filings['primaryDocument'], filings['filingDate'],)
                if form == form_filter
            ]
            
            # Return filings
            return form_filings[:count]
        
        else:
            print("Error fetching data:", response.status_code)
            return []
