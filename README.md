# SEC Filings Chatbot with RAG-based Retrieval

This project is a financial chatbot designed to help users query SEC filings, stock information, and financial news for a specific company using advanced Retrieval-Augmented Generation (RAG) techniques. It integrates various services like OpenAI, Groq, SEC API, Qdrant, and Yahoo Finance for intelligent data retrieval and processing.

## Features

- **SEC Filings Query**: Fetch and process the latest 10-K filings for a given company using the SEC API.
- **RAG System**: Combines vector retrieval from Qdrant with language models (OpenAI or Groq) to generate contextual answers based on filings and news.
- **Stock Price Information**: Retrieves the latest stock price and trading volume for any company using Yahoo Finance.
- **Financial News Scraper**: Scrapes the latest news headlines related to a specific company from Yahoo Finance.
- **Streamlit UI**: A simple web interface to interact with the chatbot, manage session histories, and display stock and filing information.
- **Multi-User Support**: Uses session IDs to separate and store data for different users.

## Setup

### Prerequisites

- Python 3.10+
- Streamlit
- Qdrant client
- OpenAI or Groq API key
- Chrome WebDriver for Selenium

### Installation

1. **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2. **Install the required Python packages**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up environment variables**:
    Create a `secrets.toml` file inside `.streamlit` folder and add the following details:
    ```
    GROQ_API_KEY="your_groq_api_key"
    QDRANT_URL="your_qdrant_url"
    QDRANT_API_KEY="your_qdrant_api_key"
    NAME = "your_name"
    EMAIL = 'address@mail.com'
    ```

4. **Running the Application**:
    To start the Streamlit app:
    ```bash
    streamlit run app.py
    ```
    This will launch the application in your default web browser.



## Usage
### Fetching SEC Filings
The `fetchfilings.py` and `qdrant_vectors_manager.py` module allows you to fetch the most recent 10-K filings for a company based on its CIK (Central Index Key). These filings are processed, chunked, and stored in a Qdrant vector store for retrieval during chat.

### RAG System
The `llmrag.py` module configures a RAG (Retrieval-Augmented Generation) chain using OpenAI or Groq models. It retrieves relevant filings sections from the vector store, formulates standalone questions, and generates answers based on the user's queries.

### Stock Prices & News
The `scraper.py` module fetches the latest stock price data using the Yahoo Finance API and scrapes the latest news articles related to a specific company.

### Chatbot Functionality
The chatbot can answer questions about:
- Recent SEC filings (10-Ks) for a company.
- Stock prices and market data for a company's stock.
- Latest financial news for a specific company.

Users can interact with the chatbot via the Streamlit interface, and the chat history is preserved for each session.


## Code Overview
### app.py
The main entry point for the application, responsible for initializing the chatbot interface in Streamlit. It manages user input, session handling, and displays results fetched from the APIs and vector store.

### fetchfilings.py
Handles:
- Providing list of companies and its CIK
- Fetching SEC filings for a specific company using its CIK.
- Fetching sections for each filings
  
### qdrant_vectors_manager.py
- Initializing a Qdrant vector store and embedding data.
- Chunking and saving 10-K filing sections into the vector store using OpenAI embeddings.

### llmrag.py
Responsible for:
- Setting up the language models (OpenAI or Groq).
- Creating a RAG chain that uses a history-aware retriever to contextualize questions.
- Configuring prompts for standalone question generation and document-based Q&A.

### scraper.py
Performs:
- Stock price data retrieval using the Yahoo Finance API.
- Scraping the latest financial news headlines for a company using BeautifulSoup and Google News website.
- Scraping the latest 50 news headlines and details for a company from Google Search > News tab