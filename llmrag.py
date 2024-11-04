
from langchain_groq import ChatGroq
from langchain_openai import OpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain


def get_llm(provider: str, api_key: str):
    """
    Get LLM for provider
    Args:
        provider: ['openai', 'groq'] (config: max_tokens=500, temp=0 (openai))
        api_key: api_key of respective provider
    Returns:
        llm
    """
    if provider.lower() == 'openai':
        model_name = "gpt-3.5-turbo-instruct"
        llm = OpenAI(model=model_name, api_key=api_key, temperature=0, max_tokens=500, max_retries=2)
    elif provider.lower() == 'groq':
        model_name = "Gemma2-9b-It"
        llm=ChatGroq(groq_api_key=api_key,model_name=model_name)
    return llm

def get_rag_chain(vectorstore, llm):
    """
    Get RAG chain from the vectorstore, llm and chat history
    The contextually related question is converted to standalone question using llm and history aware retriever
    The retrieved documents are stuffed together for retrieval
    Args:
        vectorstore: Qdrant vector store
        llm: groq, openai
    """
    # Create retriever from vectorstore
    retriever = vectorstore.as_retriever() #search_kwargs={"k": 5}
    
    # Contextualizing the question (Standalone question generation)
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question, which might reference context in the chat history, "
        "formulate a standalone question that can be understood without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )
    
    # Create rag_chain to answer standalone question obtained from history_aware_retriever using create_retrieval_chain
    qa_system_prompt = (
            "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer "
            "the question. Do not use any outside knowledge. \n\n"
            "{context}"
        )
    qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )  
    
    history_aware_retriever=create_history_aware_retriever(llm,retriever,contextualize_q_prompt)
    question_answer_chain=create_stuff_documents_chain(llm,qa_prompt)
    rag_chain=create_retrieval_chain(history_aware_retriever,question_answer_chain)

    return rag_chain
    
