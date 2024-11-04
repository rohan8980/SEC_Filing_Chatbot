import requests
from uuid import uuid4
from sec_api import ExtractorApi
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client.http.models import Distance, VectorParams
from langchain.text_splitter import RecursiveCharacterTextSplitter

def get_companies_cik(headers:dict):
    """
    Get list of company and its cik 
    Reference: "https://www.sec.gov/files/company_tickers.json"
    Args:
        headers (dict): headers for request to api
    Returns:
        (dict): dictionary of {name (ticker): cik} 
               'Apple Inc. (AAPL)': '0000320193'
    """
    company_tickers_url = "https://www.sec.gov/files/company_tickers.json"
    company_tickers = requests.get(url = company_tickers_url, headers=headers)
    company_tickers = company_tickers.json()
    company_tickers = {f"{val['title']} ({val['ticker']})": str(val['cik_str']).zfill(10) for val in company_tickers.values()}

    return company_tickers

def get_sections_10K():
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

def get_recent_filings_10K(cik: str, headers:dict, count: int=2, ):
    """
    Get SEC filings for a company by CIK (Central Index Key) from EDGAR for last 2 filings
    API Reference: https://sec-api.io/docs/sec-filings-item-extraction-api
    Args:
        cik (str): Central Index Key (CIK) of the company.
        headers (dict): headers for request to api
        count (int): N most recent 10-K filings for the company
    Returns:
        list[dict]: List of recent filings' url and date
    """
    # API URL
    base_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
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

def initialize_vectorestore(session_id: str, qdrant_client: QdrantClient, embeddings: OpenAIEmbeddings):
    """
    Initialize Qdrant Vectorstore.
    Create collection with session_id as name collection name
        Config: Vectorsize = 1536 
        Config: distance = Cosine
    """
    qdrant_client.create_collection(collection_name=session_id, vectors_config=VectorParams(size=1536, distance=Distance.COSINE),)
    return QdrantVectorStore(client=qdrant_client, collection_name=session_id, embedding=embeddings,)

def save_to_vectorstore(data: list, vector_store: QdrantVectorStore, type_of_data: str='filings', items:dict=None, extractorApi: ExtractorApi=None):
    """
    Saves data (list of text) into Qdrant vectorstore with metadata
    ExtractorApi fetches data for each section. 
    Args:
        data (list[str]): Data to be stored in vectorstore
        vector_store: Qdrant vector store
        type_of_data: ['filings', 'stock_info', 'news']
        items: 10-k filing sections dictionary (type_of_data=='filings)
        extractorApi: EDGAR API to get filings data (type_of_data=='filings)
    """
    if type_of_data == 'filings':
        # Iterating for each filing
        for filing in data:
            filing_url = filing['url']
            filing_date = filing['date']
            
            #Getting data for each section
            for item in items:
                # print("item:", item, "url", filing_url, "filing Date", filing_date, "desc", items[item])
                try:
                    uuids = []
                    metadata_list = []
                    section_desc = items[item]
                    
                    #Using extractorAPI to fetch data of each section from the form
                    section_text = extractorApi.get_section(filing_url=filing_url, section=item, return_type="text")
                    split_texts = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150).split_text(section_text)
                    for i in range(len(split_texts)):
                        uuids.append(str(uuid4())) 
                        metadata_list.append({
                            "section": section_desc,
                            "filing date": filing_date,
                            "chunk_id": f"{i}",
                        })
                    vector_store.add_texts(texts=split_texts, metadatas=metadata_list, ids=uuids)

                except Exception as e:
                    print(f"Error fetching data for {filing_url} - {item} \n{e}")
    elif type_of_data == 'stock_info':
        vector_store.add_texts(texts=[data], metadatas=[{"details": "stock"}], ids=[str(uuid4())])
    elif type_of_data == 'news':
        vector_store.add_texts(texts=[data], metadatas=[{"details": "news"}], ids=[str(uuid4())])
