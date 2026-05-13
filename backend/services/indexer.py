# Chunking & Vectorizing logic
import os
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
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


def index_website_data(url, client_id, use_sitemap=False, api_provider="google", force_reindex=False):
    """
    Index website content and store vectors in ChromaDB
    
    Args:
        url: Website URL(s) to scrape and index. Can be:
             - str: Single URL
             - list: Multiple URLs (only when use_sitemap=False)
        client_id: Unique client/shop identifier
        use_sitemap: If True, scrapes entire website using sitemap.xml
        api_provider: 'google' (default) or 'openrouter' - for embeddings during indexing
        force_reindex: If True, re-index even if data already exists (useful for updating indexed content)
        
    Returns:
        dict: Status information with indexed chunk count if new indexing, 
              or {"status": "already_indexed"} if data already exists (and force_reindex=False)
    """
    from .scraper import scrape_website, scrape_website_sitemap, scrape_multiple_urls
    
    # 1. EMBEDDINGS: Initialize first (needed for Chroma check below)
    embeddings = get_embeddings(api_provider)
    
    # Create client-specific persist directory
    client_db_path = os.path.join(Config.VECTOR_DB_PATH, client_id)
    os.makedirs(client_db_path, exist_ok=True)
    
    # Check if client already has indexed data (unless force_reindex is True)
    if not force_reindex:
        existing_db = Chroma(
            persist_directory=client_db_path,
            collection_name=client_id,
            embedding_function=embeddings
        )
        
        if len(existing_db.get()['ids']) > 0:
            print(f"✅ Data already indexed for {client_id}. Skipping...")
            print(f"💡 To re-index, set force_reindex=True or delete the database at: {client_db_path}")
            return {"status": "already_indexed", "message": f"Data for {client_id} already indexed. Use force_reindex=True to override."}
    else:
        print(f"🔄 Force re-indexing enabled for {client_id}. Clearing existing data...")
        # Delete existing database to start fresh
        import shutil
        if os.path.exists(client_db_path):
            shutil.rmtree(client_db_path)
            os.makedirs(client_db_path, exist_ok=True)
    
    # Only run if no data exists (or force_reindex is True)
    # Use sitemap scraping if requested, otherwise handle single or multiple URLs
    if use_sitemap:
        if isinstance(url, list):
            raise ValueError("use_sitemap=True but got multiple URLs. Set use_sitemap=False to scrape multiple URLs directly.")
        print(f"🌐 Using sitemap-based scraping for {url}")
        url_contents, product_urls_per_page = scrape_website_sitemap(url)  # Returns tuple (dict, dict)
    else:
        if isinstance(url, list):
            print(f"📄 Using multiple URL scraping for {len(url)} URLs")
            url_contents, product_urls_per_page = scrape_multiple_urls(url, rate_limit_delay=1, max_urls=len(url))  # Returns tuple
        else:
            print(f"📄 Using single URL scraping for {url}")
            text_content, extracted_urls = scrape_website(url)  # Now returns tuple
            url_contents = {url: text_content}
            product_urls_per_page = {url: extracted_urls}
    
    # 2. CHUNKING: Break long text into 1000-character pieces
    # Overlap ensures context isn't lost at the edges of the cut
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    
    # Process each URL separately and keep track of source URL and product links
    all_chunks = []
    all_metadatas = []
    
    for source_url, text_content in url_contents.items():
        chunks = splitter.split_text(text_content)
        all_chunks.extend(chunks)
        
        # Get product URLs found in this page
        product_urls = product_urls_per_page.get(source_url, [])
        if not product_urls:
            logger.warning(f"⚠️ No product URLs found for: {source_url}")
        
        # Tag each chunk with client_id, source_url, and product_links
        for _ in chunks:
            metadata = {
                "client_id": client_id, 
                "source_url": source_url,
                "product_links": "|".join(product_urls) if product_urls else ""  # Store as pipe-separated string
            }
            all_metadatas.append(metadata)
    
    # 4. STORAGE: Save to ChromaDB on your local disk
    vector_db = Chroma.from_texts(
        texts=all_chunks,
        metadatas=all_metadatas,
        embedding=embeddings,
        persist_directory=client_db_path,
        collection_name=client_id
    )
    if hasattr(vector_db, "persist"):
        vector_db.persist()
    
    print(f"✅ Success: Indexed {len(all_chunks)} chunks for {client_id}")
    return {"status": "success", "chunks_indexed": len(all_chunks), "message": f"Indexed {len(all_chunks)} chunks for {client_id}"}
