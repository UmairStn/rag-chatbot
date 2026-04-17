# Chunking & Vectorizing logic
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from backend.core.config import Config

def index_website_data(WEBSITE_URL, client_id):
    from .scraper import scrape_website
    
    # 1. EMBEDDINGS: Initialize first (needed for Chroma check below)
    # Using gemini-embedding-001 - the standard embedding model for Google Generative AI
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # Check if client already has indexed data
    existing_db = Chroma(
        persist_directory=Config.VECTOR_DB_PATH,
        collection_name=client_id,
        embedding_function=embeddings
    )
    
    if len(existing_db.get()['ids']) > 0:
        print(f"✅ Data already indexed for {client_id}. Skipping...")
        return
    
    # Only run if no data exists
    raw_text = scrape_website(WEBSITE_URL)
    
    # 2. CHUNKING: Break long text into 1000-character pieces
    # Overlap ensures context isn't lost at the edges of the cut
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_text(raw_text)
    
    # 3. METADATA: Tag every chunk with the client_id for security/SaaS
    metadatas = [{"client_id": client_id} for _ in chunks]
    
    # 4. STORAGE: Save to ChromaDB on your local disk
    vector_db = Chroma.from_texts(
        texts=chunks,
        metadatas=metadatas,
        embedding=embeddings,
        persist_directory=Config.VECTOR_DB_PATH
    )
    print(f"✅ Success: Indexed {len(chunks)} chunks for {client_id}")