# Chunking & Vectorizing logic
import os
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from core.config import Config

logger = logging.getLogger(__name__)

def get_embeddings(api_provider="google"):
    """
    Get embeddings model based on API provider
    
    Args:
        api_provider: 'google' or 'openrouter' (default: 'google')
        
    Returns:
        Embeddings instance
    """
    if api_provider.lower() == "openrouter":
        if not Config.OPENROUTER_API_KEY:
            raise ValueError("❌ OPENROUTER_API_KEY not configured")
        from langchain_openai import OpenAIEmbeddings
        logger.info("🔗 Using OpenRouter embeddings")
        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=Config.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
    else:
        # Default to Google
        logger.info("🔗 Using Google embeddings")
        return GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


def index_website_data(url, client_id, use_sitemap=False, api_provider="google"):
    """
    Index website content and store vectors in ChromaDB
    
    Args:
        url: Website URL(s) to scrape and index. Can be:
             - str: Single URL
             - list: Multiple URLs (only when use_sitemap=False)
        client_id: Unique client/shop identifier
        use_sitemap: If True, scrapes entire website using sitemap.xml
        api_provider: 'google' (default) or 'openrouter' - for embeddings during indexing
        
    Returns:
        dict: Status information with indexed chunk count if new indexing, 
              or {"status": "already_indexed"} if data already exists
    """
    from .scraper import scrape_website, scrape_website_sitemap, scrape_multiple_urls
    
    # 1. EMBEDDINGS: Initialize first (needed for Chroma check below)
    embeddings = get_embeddings(api_provider)
    
    # Create client-specific persist directory
    client_db_path = os.path.join(Config.VECTOR_DB_PATH, client_id)
    os.makedirs(client_db_path, exist_ok=True)
    
    # Check if client already has indexed data
    existing_db = Chroma(
        persist_directory=client_db_path,
        collection_name=client_id,
        embedding_function=embeddings
    )
    
    if len(existing_db.get()['ids']) > 0:
        print(f"✅ Data already indexed for {client_id}. Skipping...")
        return {"status": "already_indexed", "message": f"Data for {client_id} already indexed"}
    
    # Only run if no data exists
    # Use sitemap scraping if requested, otherwise handle single or multiple URLs
    if use_sitemap:
        if isinstance(url, list):
            raise ValueError("use_sitemap=True but got multiple URLs. Set use_sitemap=False to scrape multiple URLs directly.")
        print(f"🌐 Using sitemap-based scraping for {url}")
        raw_text = scrape_website_sitemap(url)
    else:
        if isinstance(url, list):
            print(f"📄 Using multiple URL scraping for {len(url)} URLs")
            raw_text = scrape_multiple_urls(url, rate_limit_delay=1, max_urls=len(url))
        else:
            print(f"📄 Using single URL scraping for {url}")
            raw_text = scrape_website(url)
    
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
        persist_directory=client_db_path,
        collection_name=client_id
    )
    
    print(f"✅ Success: Indexed {len(chunks)} chunks for {client_id}")
    return {"status": "success", "chunks_indexed": len(chunks), "message": f"Indexed {len(chunks)} chunks for {client_id}"}