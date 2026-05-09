import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from core.config import Config

# ============================================================================
# MANUAL API CONTROL FOR CHAT (Backend Configuration)
# ============================================================================
# Change this value to switch which API is used for chat responses
# Options: "google" or "openrouter"
CHAT_API_PROVIDER = "google"
# ============================================================================

def get_chatbot_response(user_query, client_id):
    """
    Get response from chatbot using the configured API provider
    
    API provider is set by CHAT_API_PROVIDER constant at the top of this file.
    To switch APIs, edit CHAT_API_PROVIDER = "google" or "openrouter"
    """
    # Get LLM based on configured provider
    if CHAT_API_PROVIDER == "openrouter":
        if not Config.OPENROUTER_API_KEY:
            raise ValueError("❌ OPENROUTER_API_KEY not configured for chat")
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model="openrouter/auto",
            api_key=Config.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
    else:
        # Default to Google
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",convert_system_message_to_human=True)
    
    # Using gemini-embedding-001 - the standard embedding model for Google Generative AI
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # Use client-specific persist directory
    client_db_path = os.path.join(Config.VECTOR_DB_PATH, client_id)
    db = Chroma(persist_directory=client_db_path, embedding_function=embeddings, collection_name=client_id)
    
    # Setup the retriever with your multi-tenant filter
    retriever = db.as_retriever(search_kwargs={'filter': {'client_id': client_id}})

    # Define the system instructions
    system_prompt = (
        "You are a helpful assistant. Use the following pieces of retrieved "
        "context to answer the question. If you don't know the answer, say that "
        "you don't know.\n\n"
        "{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # Create the modern chain
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    # Invoke the chain
    response = rag_chain.invoke({"input": user_query})
    return response["answer"]