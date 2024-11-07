from uuid import uuid4
from sec_api import ExtractorApi
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client.http.models import Distance, VectorParams
from langchain.text_splitter import RecursiveCharacterTextSplitter

class QdrantVectorsManager:

    def initialize_vectorstore(self, collection_name: str, qdrant_client: QdrantClient, embeddings: OpenAIEmbeddings) -> QdrantVectorStore:
        """
        Initialize Qdrant Vectorstore
        Create collection with collection name
            Config: Vectorsize = 1536 
            Config: distance = Cosine
        """
        qdrant_client.create_collection(collection_name=collection_name, vectors_config=VectorParams(size=1536, distance=Distance.COSINE),)
        return QdrantVectorStore(client=qdrant_client, collection_name=collection_name, embedding=embeddings,)

    def save_to_vectorstore(self, data: list, vector_store: QdrantVectorStore, type_of_data: str='filings', sections:dict=None, extractorApi: ExtractorApi=None):
        """
        Saves data (list of text) into Qdrant vectorstore with metadata
        ExtractorApi fetches data for each section. 
        Args:
            data (list[str]): Data to be stored in vectorstore
            vector_store: Qdrant vector store
            type_of_data: ['filings', 'stock_info', 'news']
            sections: 10-k filing sections dictionary (type_of_data=='filings)
            extractorApi: EDGAR API to get filings data (type_of_data=='filings)
        """
        if type_of_data == 'filings':
            # Iterating for each filing
            for filing in data:
                filing_url = filing['url']
                filing_date = filing['date']
                
                #Getting data for each section
                for item in sections:
                    # print("item:", item, "url", filing_url, "filing Date", filing_date, "desc", sections[item])
                    try:
                        uuids = []
                        metadata_list = []
                        section_desc = sections[item]
                        
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
            vector_store.add_texts(texts=[data], metadatas=[{"details": "stock", "chunk_id": "0"}], ids=[str(uuid4())])
        elif type_of_data == 'news':
            if len(data) > 1500:
                split_texts = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150).split_text(data)
                uuids, metadata_list = [], []
                for i in range(len(split_texts)):
                    uuids.append(str(uuid4())) 
                    metadata_list.append({
                        "details": "news",
                        "chunk_id": f"{i}",
                    })
                vector_store.add_texts(texts=split_texts, metadatas=metadata_list, ids=uuids)
            else:
                vector_store.add_texts(texts=[data], metadatas=[{"details": "news"}], ids=[str(uuid4())])
