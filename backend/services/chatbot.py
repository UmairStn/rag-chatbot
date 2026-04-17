from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from backend.core.config import Config

def get_chatbot_response(user_query, client_id):
    # Using gemini-embedding-001 - the standard embedding model for Google Generative AI
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    db = Chroma(persist_directory=Config.VECTOR_DB_PATH, embedding_function=embeddings)
    
    # Setup the retriever with your multi-tenant filter
    retriever = db.as_retriever(search_kwargs={'filter': {'client_id': client_id}})
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

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