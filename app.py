import os
import datetime
import warnings
import streamlit as st
from llmrag import LlmRag
from scraper import Scraper
from fetchfilings import FetchFilings
from sec_api import ExtractorApi
from qdrant_vectors_manager import QdrantVectorsManager
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory
warnings.simplefilter(action='ignore', category=FutureWarning)


# Setting up api keys and env variables from secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
QDRANT_URL = st.secrets["QDRANT_URL"]
QDRANT_API_KEY = st.secrets["QDRANT_API_KEY"]
NAME = st.secrets["NAME"]
EMAIL = st.secrets["EMAIL"]
headers = {"User-Agent": f"{NAME} {EMAIL}",}
llm_rag = LlmRag()
fetch_filings = FetchFilings(headers)
qdrant_vectorstore = QdrantVectorsManager()
embedding_model_openai = "text-embedding-3-small"
show_recent_n_chats = 10
fetch_recent_n_years_filings = 5


# Streamlit UI: Session variables for UI
if 'is_configured' not in st.session_state:
    st.session_state.is_configured = False
if 'data_fetched' not in st.session_state:
    st.session_state.data_fetched = False

# Utility Functions to manage UI
def get_new_session():
    """
    Get new session id based on current datetime.
    sets session variable session_id
    """
    now = datetime.datetime.now()
    st.session_state.session_id = now.strftime("%Y%m%d%H%M%S%f")
def get_current_session():
    """
    Get current session id from session state
    """
    return st.session_state.session_id
def get_session_history(session_id:str)->BaseChatMessageHistory:
    """
    Get chat history based on provided session
    Args:
        session_id (str): history to be fetched for session id
    Returns:
        store (BaseChatMessageHistory): chat history of provided session id
    """
    session_id = get_current_session() if not session_id else session_id
    if session_id not in st.session_state.store:
        st.session_state.store[session_id]=ChatMessageHistory()
    return st.session_state.store[session_id]
def trim_chat_history(session_id, n:int = 10):
    """
    Keep only last 'n' conversations in the chat history
    Args:
        Session_id: session id for which chats to remove
        n: number of chats to keep
    """
    if session_id not in st.session_state.store:
        return
    qa_pairs = []
    temp_pair = []
    chat_history = st.session_state.store[session_id].messages

    for message in chat_history:
        if isinstance(message, HumanMessage):
            # When HumanMessage starts, save any previous pair and start a new one
            if temp_pair:
                qa_pairs.append(temp_pair)
            temp_pair = [message]
        elif isinstance(message, AIMessage):
            # Append AI response to the current pair
            if temp_pair:
                temp_pair.append(message)
                qa_pairs.append(temp_pair)
                temp_pair = []
    # Last temp_pair (AI Message) added 
    if temp_pair:
        qa_pairs.append(temp_pair)
    
    # Keep last n conversations
    trimmed_history = qa_pairs[-n:]
    st.session_state.store[session_id].messages = [msg for pair in trimmed_history for msg in pair]

    return st.session_state.store[session_id].messages
def show_chat_history(session_id=None, last_n_chats: int=2):
    """
    Fetches chat history from store{} for provided session_id after keeping only n latest chats
    Args:
        session_id (str): Session Id for which chat history to be fetched
        last_n_chats (int): Show only Last 'n' chats for the provided session ID
    """
    st.markdown("""
        <style>
        .human-message {
            text-align: right;
            background: linear-gradient(135deg, #a8e063, #56ab2f);
            padding: 14px;
            border-radius: 20px 20px 0 20px;
            margin-bottom: 12px;
            box-shadow: 0px 5px 10px rgba(0, 0, 0, 0.15);
            max-width: 65%;
            margin-left: auto;
            font-family: 'Roboto', sans-serif;
            font-size: 15px;
            color: #fff;
            animation: fade-slide-in 0.4s ease;
        }

        .ai-message {
            text-align: left;
            background: linear-gradient(135deg, #f0f0f0, #cccccc);
            padding: 14px;
            border-radius: 20px 20px 20px 0;
            margin-bottom: 12px;
            box-shadow: 0px 5px 10px rgba(0, 0, 0, 0.15);
            max-width: 65%;
            margin-right: auto;
            font-family: 'Roboto', sans-serif;
            font-size: 15px;
            color: #333;
            animation: fade-slide-in 0.4s ease;
        }

        @keyframes fade-slide-in {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        </style>
        """, unsafe_allow_html=True)

    session_id = get_current_session() if not session_id else session_id
    trim_chat_history(session_id, last_n_chats)
    chat_history = get_session_history(session_id).messages
    for message in chat_history:
        if isinstance(message, AIMessage):
            message_content = message.content
            message_content = message_content.split("AI:", 1)[1].strip() if "AI:" in message_content else message_content
            message_content = message_content.split("System: ", 1)[1].strip() if "System: " in message_content else message_content
            st.markdown(f"<div class='ai-message'>{message_content}</div>", unsafe_allow_html=True)
        elif isinstance(message, HumanMessage):
            st.markdown(f"<div class='human-message'>{message.content}</div>", unsafe_allow_html=True)
def clear_input():
    """
    Clear chat input text box to stop it from rerunning again when stremlit ui reloads
    """
    st.session_state.query=st.session_state.text_input
    st.session_state.text_input=""  

# UI Components
st.title("SEC Filing (10-K) Q&A")

# Sidebar for API keys and LLM selection
st.sidebar.title("Configurations")
llm_provider = st.sidebar.selectbox("Select LLM Company", ["Groq", "OpenAI",])
openai_api_key = st.sidebar.text_input("OpenAI [API Key](https://platform.openai.com/api-keys) - Embeddings", type="password")
sec_api_key = st.sidebar.text_input("SEC Filings - Edgar [API Key](https://sec-api.io/)", type="password")

# Configure Button to process and initialize everything
if st.sidebar.button("Configure"):
    # Error if anything is missing
    if not llm_provider:
        st.sidebar.error("Please select a valid llm provider.")
    elif not openai_api_key:
        st.sidebar.error("Please enter a valid OpenAI API key.")
    elif not sec_api_key:
        st.sidebar.error("Please enter a valid SEC API Key.")
    # Else initialize session variables
    else:
        # Setting up session variables
        if 'store' not in st.session_state:
            st.session_state.store={}
        if 'session_id' not in st.session_state:
            get_new_session()
        if 'llm' not in st.session_state:
            api_key = openai_api_key if llm_provider == "OpenAI" else GROQ_API_KEY if llm_provider == 'Groq' else None
            st.session_state.llm = llm_rag.get_llm(provider=llm_provider, api_key=api_key)
        if 'extractorApi' not in st.session_state:
            st.session_state.extractorApi = ExtractorApi(sec_api_key)
        if 'qdrant_client' not in st.session_state:
            st.session_state.qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY,)
        if 'embeddings' not in st.session_state:
            st.session_state.embeddings = OpenAIEmbeddings(model=embedding_model_openai, openai_api_key=openai_api_key)
        if 'vector_store' not in st.session_state:
            st.session_state.vector_store = qdrant_vectorstore.initialize_vectorstore(collection_name = st.session_state.session_id, 
                                                                            qdrant_client = st.session_state.qdrant_client,
                                                                            embeddings = st.session_state.embeddings)
        if 'query' not in st.session_state:
            st.session_state.query=""
        if 'last_n_chats' not in st.session_state:
            st.session_state.last_n_chats = show_recent_n_chats
        if 'sections' not in st.session_state:
            st.session_state.sections = fetch_filings.get_sections_10K()

        st.session_state.is_configured = True
    

# Main Screen
if st.session_state.is_configured:
    # Getting list of companies and cik from EDGAR
    company_tickers = fetch_filings.get_companies_cik()
    selected_company = st.selectbox("Choose a company", [""] +list(company_tickers.keys()))
    if selected_company:
        # Getting Cik from the Selected Company
        cik = company_tickers[selected_company]
        selected_filings = []
        # Fetching 10K filings using cik of the selected company
        filings = fetch_filings.get_recent_filings_10K(cik=cik, count=fetch_recent_n_years_filings) # Limit max to 5 years filings

        # Checkbox for 10k filings based on filing dates
        st.write("###### Select filings")
        selected_filings = []
        cols_per_row = 5
        num_filings = len(filings)
        for i in range(0, num_filings, cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < num_filings:
                    filing = filings[i + j]
                    with col:
                        if st.checkbox(filing['date']):
                            selected_filings.append(filing)
        # Checkbox for "Search Web"
        st.write('###### Search Web?')
        col1, col2, col3 = st.columns([1, 1, 1])  
        with col1:
            search_web = st.checkbox("Search Web")
        filings = selected_filings

        # Checkbox for 10K Sections for a filing
        st.write("###### Select Sections for filing")
        cols_per_row = 2
        selected_sections = {}
        sections = list(st.session_state.sections.items())
        num_sections = len(sections)
        for i in range(0, num_sections, cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < num_sections:
                    item_key, item_value = sections[i + j]
                    with col:
                        if st.checkbox(f"{item_key}: {item_value[:70]}", value=True):
                            selected_sections[item_key] = item_value

        # Fetch Data Button to gather data and save it in Qdrant VectorStore
        if st.button("Fetch Data"):
            st.session_state.sections = selected_sections
            with st.spinner('Extracting data from EDGAR API...'):
                qdrant_vectorstore.save_to_vectorstore(data=filings, vector_store=st.session_state.vector_store, type_of_data='filings', sections=st.session_state.sections, extractorApi=st.session_state.extractorApi)
                # st.write("Selected filings have been processed and saved to the vector store.")
            if search_web:
                ticker = selected_company.split('(')[-1].strip(') ')
                webscraper = Scraper(ticker)
                with st.spinner('Gathering stock info from web..'):
                    stock_info = webscraper.get_stock_info()
                    qdrant_vectorstore.save_to_vectorstore(data=stock_info, vector_store=st.session_state.vector_store, type_of_data='stock_info')
                with st.spinner('Gathering latest news from web..'):
                    news_info = webscraper.get_finance_news()
                    qdrant_vectorstore.save_to_vectorstore(data=news_info, vector_store=st.session_state.vector_store, type_of_data='news')
                # st.write(f"Web data for {selected_company} has been scraped and saved to the vector store.")
            
            st.session_state.data_fetched = True
        
    # Begin Q&A after vectorstore    
    if st.session_state.data_fetched:
        # Prepare RAG Chain from vectorestore and llm
        rag_chain = llm_rag.get_rag_chain(vectorstore = st.session_state.vector_store, llm = st.session_state.llm) 

        # Chat history container
        chat_placeholder = st.empty()
        with chat_placeholder.container():
            show_chat_history()

        # Taking user Query and getting answer from LLM
        st.text_input(placeholder="Ask your question here", label="Question", label_visibility="collapsed", key='text_input', on_change=clear_input)
        if st.session_state.query:
            with st.spinner('Thinking...'):
                config = {"configurable": {"session_id":get_current_session()}}
                conversational_rag_chain=RunnableWithMessageHistory(rag_chain, get_session_history, input_messages_key="input", history_messages_key="chat_history", output_messages_key="answer")
                response = conversational_rag_chain.invoke({"input": st.session_state.query}, config=config)
            st.session_state.query = ""
            
        with chat_placeholder.container():
            show_chat_history(last_n_chats=st.session_state.last_n_chats)