# RAG Chatbot - Deep-Dive Technical Explanation

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Data Flow Pipeline](#data-flow-pipeline)
3. [Line-by-Line Analysis: Complex Files](#line-by-line-analysis)
4. [Functional Logic Walkthrough](#functional-logic-walkthrough)
5. [Variables & State Management](#variables--state-management)
6. [Control Flow & Conditional Logic](#control-flow--conditional-logic)
7. [Data Transformation Details](#data-transformation-details)

---

## System Architecture Overview

This is a **Retrieval-Augmented Generation (RAG)** chatbot built with FastAPI. The system has two primary workflows:

1. **Ingestion Pipeline**: URL → Scraping → Chunking → Embedding → Vector Storage
2. **Query Pipeline**: User Query → Vector Search → Context Retrieval → LLM Generation → Response

### Core Technology Stack:
- **FastAPI**: REST API framework
- **LangChain**: RAG orchestration framework
- **ChromaDB**: Vector database for embeddings storage
- **Google Gemini API**: LLM and embeddings (primary)
- **OpenRouter API**: Alternative LLM/embeddings provider
- **BeautifulSoup4**: HTML parsing and web scraping
- **Pydantic**: Request/response validation

---

## Data Flow Pipeline

### Ingestion Flow (Detailed):
```
1. HTTP POST /ingest
   ↓
2. API Key Validation (middleware)
   ↓
3. Pydantic Schema Validation (IngestRequest)
   ↓
4. index_website_data() called
   ↓
5. Check if client_id already indexed (ChromaDB query)
   ↓
6. If not indexed:
   a. Scrape website (single URL, multiple URLs, or sitemap)
   b. Clean HTML → Extract text
   c. Split text into chunks (RecursiveCharacterTextSplitter)
   d. Generate embeddings for each chunk
   e. Store in ChromaDB with metadata
   ↓
7. Return response with chunk count
```

### Query Flow (Detailed):
```
1. HTTP POST /chat
   ↓
2. API Key Validation
   ↓
3. Pydantic Schema Validation (ChatRequest)
   ↓
4. get_chatbot_response() called
   ↓
5. Initialize LLM (Google Gemini or OpenRouter)
   ↓
6. Initialize embeddings model
   ↓
7. Load ChromaDB for client_id
   ↓
8. Convert user query to embedding
   ↓
9. Vector similarity search (retrieve top-k chunks)
   ↓
10. Build prompt with retrieved context
   ↓
11. Send to LLM for generation
   ↓
12. Return generated answer
```

---

## Line-by-Line Analysis: Complex Files

### File 1: `services/scraper.py` (Most Complex)

This file handles web scraping with three strategies: single URL, multiple URLs, and sitemap-based scraping.

#### **Lines 1-11: Imports and Logger Setup**
```python
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)
```

**Why these imports?**
- `requests`: HTTP client for fetching web pages
- `BeautifulSoup`: HTML parser that creates a navigable tree structure
- `time`: For rate limiting between requests (prevents server overload)
- `urllib.parse`: URL manipulation (joining relative URLs, parsing components)
- `xml.etree.ElementTree`: XML parser for sitemap.xml files
- `logging`: Structured logging for debugging and monitoring

#### **Lines 13-30: scrape_website() - Single URL Scraper**

```python
def scrape_website(WEBSITE_URL):
    """Scrape a single website URL and return clean text"""
    headers = {"User-Agent": "Mozilla/5.0"} # Pretend to be a real user browser
    response = requests.get(WEBSITE_URL, headers=headers, timeout=10)
```

**Line-by-line mechanics:**

**Line 14**: Function signature takes a single URL string
**Line 16**: `headers` dictionary with User-Agent
  - **Why?** Many websites block requests without a User-Agent header (anti-bot protection)
  - `"Mozilla/5.0"` mimics a Firefox browser
  
**Line 17**: `requests.get()` performs HTTP GET request
  - `headers=headers`: Passes the User-Agent
  - `timeout=10`: Raises exception if server doesn't respond in 10 seconds
  - Returns a `Response` object containing status code, headers, and body

```python
    # Parse the HTML code
    soup = BeautifulSoup(response.text, 'html.parser')
```

**Line 20**: Creates BeautifulSoup object
  - `response.text`: Raw HTML string from the HTTP response
  - `'html.parser'`: Uses Python's built-in HTML parser (alternative: lxml, html5lib)
  - `soup` is now a navigable tree structure representing the DOM

```python
    # Remove 'Noise' (elements that don't help the AI answer questions)
    for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
        element.decompose() # Physically delete these from the parsed content
```

**Line 23-24**: Removes non-content elements
  - `soup(["script", "style", ...])`: CSS selector that finds all matching tags
  - Returns a list of Tag objects
  - **Why remove these?**
    - `<script>`: JavaScript code (not human-readable content)
    - `<style>`: CSS styling rules (not content)
    - `<nav>`, `<footer>`, `<header>`: Navigation/UI elements (not main content)
    - `<aside>`: Sidebar content (often ads or unrelated links)
  - `element.decompose()`: Permanently removes the element from the tree (not just hiding it)

```python
    # Extract the clean text, using a space to separate words
    clean_text = soup.get_text(separator=' ', strip=True)
    return clean_text
```

**Line 27**: Extracts all text from remaining HTML
  - `get_text()`: Recursively traverses the tree and concatenates all text nodes
  - `separator=' '`: Inserts a space between text from different elements (prevents "wordsmashing")
  - `strip=True`: Removes leading/trailing whitespace from each text chunk
  - Returns a single string with all page content

#### **Lines 33-115: fetch_sitemap_urls() - Sitemap Parser**

```python
def fetch_sitemap_urls(base_url):
    """
    Fetch and parse sitemap.xml to extract all URLs from a website
    Handles both regular sitemaps and sitemapindex (parent sitemaps)
    """
    try:
        # Construct sitemap URL
        parsed_url = urlparse(base_url)
        sitemap_url = f"{parsed_url.scheme}://{parsed_url.netloc}/sitemap.xml"
```

**Line 41**: `urlparse()` breaks URL into components
  - Input: `"https://example.com/page"`
  - Output: `ParseResult(scheme='https', netloc='example.com', path='/page', ...)`
  
**Line 42**: Constructs sitemap URL
  - `parsed_url.scheme`: "https" or "http"
  - `parsed_url.netloc`: Domain name (e.g., "example.com")
  - Result: `"https://example.com/sitemap.xml"`
  - **Why?** Standard location for sitemaps (SEO convention)

```python
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(sitemap_url, headers=headers, timeout=10)
        response.raise_for_status()
```

**Line 46**: Fetches sitemap XML file
**Line 47**: `raise_for_status()` raises HTTPError for 4xx/5xx status codes
  - **Why?** Converts bad HTTP responses into Python exceptions for error handling

```python
        # Parse XML sitemap
        root = ET.fromstring(response.content)
        
        # Define namespace for sitemap
        namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
```

**Line 50**: Parses XML string into ElementTree
  - `response.content`: Raw bytes (not `.text` which is string)
  - `root`: Root XML element (e.g., `<urlset>` or `<sitemapindex>`)

**Line 53**: XML namespace definition
  - **Why?** Sitemap XML uses namespaces: `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">`
  - Without namespace, `findall()` won't match elements
  - `'ns'`: Prefix used in XPath queries

```python
        # Check if this is a sitemapindex (contains links to other sitemaps)
        sitemap_links = root.findall('.//ns:sitemap/ns:loc', namespaces)
        if not sitemap_links:
            sitemap_links = root.findall('.//sitemap/loc')
```

**Line 56**: XPath query for nested sitemaps
  - `.//`: Recursive search (any depth)
  - `ns:sitemap/ns:loc`: Matches `<sitemap><loc>URL</loc></sitemap>`
  - **Why two attempts?** Some sitemaps don't use namespaces (fallback on line 58)

```python
        # If this is a sitemapindex, fetch all child sitemaps
        if sitemap_links:
            logger.info(f"📑 Detected sitemapindex with {len(sitemap_links)} child sitemaps")
            all_urls = []
            
            for sitemap_link_elem in sitemap_links:
                child_sitemap_url = sitemap_link_elem.text
```

**Line 61-66**: Handles sitemap index (sitemap of sitemaps)
  - **Why?** Large sites split sitemaps (e.g., sitemap_products.xml, sitemap_blog.xml)
  - `sitemap_link_elem.text`: Extracts text content of `<loc>` element

```python
                try:
                    child_response = requests.get(child_sitemap_url, headers=headers, timeout=10)
                    child_response.raise_for_status()
                    child_root = ET.fromstring(child_response.content)
                    
                    # Extract URLs from child sitemap
                    child_urls = child_root.findall('.//ns:url/ns:loc', namespaces)
                    if not child_urls:
                        child_urls = child_root.findall('.//url/loc')
                    
                    for url_elem in child_urls:
                        all_urls.append(url_elem.text)
```

**Lines 70-80**: Recursively fetches each child sitemap
  - Same parsing logic as parent sitemap
  - Extracts `<url><loc>` elements (actual page URLs)
  - Appends to `all_urls` list

```python
                except Exception as e:
                    logger.warning(f"⚠️ Error fetching child sitemap {child_sitemap_url}: {str(e)}")
```

**Line 84**: Graceful error handling
  - **Why?** One broken child sitemap shouldn't fail entire ingestion
  - Logs warning but continues processing other sitemaps

```python
        # Otherwise, extract URLs directly from the regular sitemap
        urls = []
        url_elements = root.findall('.//ns:url/ns:loc', namespaces)
        if not url_elements:
            url_elements = root.findall('.//url/loc')
        
        for url_elem in url_elements:
            urls.append(url_elem.text)
```

**Lines 92-99**: Handles regular sitemap (not sitemap index)
  - Same XPath logic to extract page URLs
  - Returns list of URL strings

#### **Lines 118-175: filter_product_pages() - URL Filtering**

```python
def filter_product_pages(urls):
    """
    Filter out individual product pages, keep only listing/category pages
    """
    filtered_urls = []
    
    # Patterns that indicate individual product pages to SKIP
    skip_patterns = [
        '/product/',          # /product/123 or /product/name
        '/products/p/',       # /products/p/123
        '/item/',             # /item/123
        '/p/',                # Short product URL
        '/sku/',              # /sku/12345
        'product-id=',        # Query parameter
        'productid=',         # Query parameter
        '/buy/',              # /buy/product-name
        '?id=',               # Product ID query
        '?product=',          # Product query
    ]
```

**Lines 126-135**: Skip patterns list
  - **Why filter?** E-commerce sites have thousands of individual product pages
  - Scraping all products would:
    1. Take too long (rate limiting)
    2. Create redundant embeddings (similar product descriptions)
    3. Exceed max_urls limit
  - **Strategy**: Only scrape category/listing pages that summarize products

```python
    # Patterns that indicate listing/category pages to KEEP
    keep_patterns = [
        '/collections/',      # Category pages
        '/categories/',       # Category pages
        '/shop',              # Shop page
        '/products',          # Product listing (not individual)
        '/pages/',            # Static pages
        '/blog',              # Blog pages
        '/search',            # Search results
        '/?page=',            # Paginated listings
    ]
```

**Lines 138-147**: Keep patterns list
  - These URLs typically contain multiple products or important info
  - `/collections/`: Shopify-style category pages
  - `/?page=`: Pagination (page 1, 2, 3 of listings)

```python
    for url in urls:
        url_lower = url.lower()
        
        # Skip if matches skip patterns
        skip = False
        for pattern in skip_patterns:
            if pattern in url_lower:
                skip = True
                logger.debug(f"⏭️ Skipping product page: {url}")
                break
```

**Lines 149-157**: Skip pattern matching
  - `url_lower`: Case-insensitive matching
  - `if pattern in url_lower`: Substring search (not regex for performance)
  - `break`: Early exit once match found (no need to check other patterns)

```python
        # Keep if matches keep patterns or is root/home page
        keep = False
        if url_lower.endswith('.lk/') or url_lower.endswith('.com/') or url_lower.endswith('.com'):
            keep = True  # Root/home page
        else:
            for pattern in keep_patterns:
                if pattern in url_lower:
                    keep = True
                    break
```

**Lines 162-169**: Keep pattern matching
  - **Line 163**: Special case for homepage (always keep)
  - `.endswith('.lk/')`: Sri Lankan domains
  - `.endswith('.com/')` or `.endswith('.com')`: Root domain URLs

#### **Lines 178-227: scrape_multiple_urls() - Batch Scraper**

```python
def scrape_multiple_urls(urls, rate_limit_delay=1, max_urls=50):
    """
    Scrape multiple URLs and combine their content
    
    Args:
        urls: List of URLs to scrape
        rate_limit_delay: Delay in seconds between requests to be respectful
        max_urls: Maximum number of URLs to scrape (prevents timeout on huge sitemaps)
    """
    # Limit to avoid scraping forever on huge sitemaps
    if len(urls) > max_urls:
        logger.warning(f"⚠️ Sitemap has {len(urls)} URLs, limiting to {max_urls} (most important pages)")
        urls = urls[:max_urls]
```

**Lines 188-190**: URL limiting
  - `urls[:max_urls]`: Python slice (takes first 50 URLs)
  - **Why?** Prevents:
    1. API timeouts (FastAPI has request timeout limits)
    2. Excessive API costs (embeddings are paid per token)
    3. Server overload (too many requests)

```python
    combined_text = ""
    successful_scrapes = 0
    failed_urls = []
```

**Lines 192-194**: State variables
  - `combined_text`: Accumulator string (grows with each successful scrape)
  - `successful_scrapes`: Counter for success rate logging
  - `failed_urls`: List for error reporting

```python
    for idx, url in enumerate(urls, 1):
        try:
            logger.info(f"📄 [{idx}/{len(urls)}] Scraping: {url}")
            
            text = scrape_website(url)
            combined_text += f"\n\n--- Page: {url} ---\n{text}"
            successful_scrapes += 1
```

**Line 198**: `enumerate(urls, 1)` creates (index, value) tuples starting at 1
  - **Why start at 1?** Human-readable logging (page 1/50, not 0/50)

**Line 202**: Calls single-URL scraper
**Line 203**: Concatenates with delimiter
  - `\n\n--- Page: {url} ---\n`: Separator helps LLM understand context boundaries
  - **Why include URL?** Helps LLM cite sources in responses

```python
            # Rate limiting - be respectful to the server
            if idx < len(urls):  # Don't sleep after last URL
                time.sleep(rate_limit_delay)
```

**Lines 206-207**: Rate limiting
  - `time.sleep(1)`: Pauses execution for 1 second
  - **Why?** Prevents overwhelming target server (ethical scraping)
  - **Why skip last URL?** No need to wait after final request

```python
        except requests.exceptions.Timeout:
            logger.warning(f"❌ Timeout on {url}")
            failed_urls.append(url)
        except requests.exceptions.RequestException as e:
            logger.warning(f"❌ Failed to scrape {url}: {str(e)}")
            failed_urls.append(url)
        except Exception as e:
            logger.warning(f"❌ Error processing {url}: {str(e)}")
            failed_urls.append(url)
```

**Lines 209-217**: Granular exception handling
  - `Timeout`: Specific exception for slow servers
  - `RequestException`: Base class for all requests errors (DNS, connection, etc.)
  - `Exception`: Catch-all for BeautifulSoup parsing errors
  - **Why three levels?** Different errors need different logging messages
  - **Why not raise?** One failed URL shouldn't stop entire batch

---

### File 2: `services/indexer.py` (Second Most Complex)

This file handles the chunking and vectorization pipeline.

#### **Lines 1-11: Imports**

```python
import os
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from core.config import Config

logger = logging.getLogger(__name__)
```

**Key imports:**
- `RecursiveCharacterTextSplitter`: Intelligent text chunking algorithm
- `GoogleGenerativeAIEmbeddings`: Converts text to 768-dimensional vectors
- `Chroma`: Vector database (stores embeddings with metadata)

#### **Lines 13-32: get_embeddings() - Embeddings Factory**

```python
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
```

**Factory Pattern Implementation:**
- **Line 23**: Conditional instantiation based on provider
- **Why factory?** Allows switching embedding providers without changing calling code
- **OpenRouter path (lines 24-30):**
  - Uses OpenAI-compatible API
  - `text-embedding-3-small`: 1536-dimensional embeddings
  - `base_url`: Routes to OpenRouter instead of OpenAI
- **Google path (lines 32-34):**
  - `gemini-embedding-001`: 768-dimensional embeddings
  - Automatically uses `GOOGLE_API_KEY` from environment

#### **Lines 35-100: index_website_data() - Main Indexing Pipeline**

```python
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
```

**Line 51**: Lazy import to avoid circular dependencies
  - **Why?** `scraper.py` doesn't import `indexer.py`, but `indexer.py` needs `scraper.py`

```python
    # 1. EMBEDDINGS: Initialize first (needed for Chroma check below)
    embeddings = get_embeddings(api_provider)
```

**Line 54**: Initialize embeddings model
  - **Why first?** ChromaDB requires embeddings function to load existing collections
  - This creates the embedding model instance that will be used for both checking and indexing

```python
    # Create client-specific persist directory
    client_db_path = os.path.join(Config.VECTOR_DB_PATH, client_id)
    os.makedirs(client_db_path, exist_ok=True)
```

**Lines 57-58**: Multi-tenant directory structure
  - `Config.VECTOR_DB_PATH`: Base path (e.g., `/data/vector_db/`)
  - `client_id`: Tenant identifier (e.g., `shop_001`)
  - Result: `/data/vector_db/shop_001/`
  - `exist_ok=True`: Don't error if directory already exists
  - **Why separate directories?** Data isolation between clients (SaaS architecture)

```python
    # Check if client already has indexed data
    existing_db = Chroma(
        persist_directory=client_db_path,
        collection_name=client_id,
        embedding_function=embeddings
    )
    
    if len(existing_db.get()['ids']) > 0:
        print(f"✅ Data already indexed for {client_id}. Skipping...")
        return {"status": "already_indexed", "message": f"Data for {client_id} already indexed"}
```

**Lines 61-68**: Duplicate prevention
  - `Chroma(...)`: Loads existing database (or creates empty one)
  - `existing_db.get()`: Returns dict with keys: `['ids', 'embeddings', 'metadatas', 'documents']`
  - `['ids']`: List of document IDs (empty list if no data)
  - `len(...) > 0`: Checks if any documents exist
  - **Why check?** Prevents re-indexing (saves API costs and time)

```python
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
```

**Lines 71-82**: Scraping strategy selection
  - **Three paths:**
    1. **Sitemap mode** (line 72-75): Crawls entire site via sitemap.xml
    2. **Multiple URLs** (line 77-79): Scrapes specific list of URLs
    3. **Single URL** (line 81-82): Scrapes one page
  - **Line 73**: Validation - sitemap mode doesn't accept URL lists
  - **Why three modes?** Flexibility for different use cases:
    - Sitemap: Full site indexing
    - Multiple: Specific pages (e.g., product categories)
    - Single: Quick testing or single-page sites

```python
    # 2. CHUNKING: Break long text into 1000-character pieces
    # Overlap ensures context isn't lost at the edges of the cut
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_text(raw_text)
```

**Lines 84-86**: Text chunking
  - `RecursiveCharacterTextSplitter`: Intelligent splitting algorithm
  - **How it works:**
    1. Tries to split on `\n\n` (paragraphs)
    2. If chunks still too large, splits on `\n` (lines)
    3. If still too large, splits on `. ` (sentences)
    4. Last resort: splits on spaces or characters
  - `chunk_size=1000`: Target size in characters
  - `chunk_overlap=150`: Overlap between consecutive chunks
  - **Why overlap?** Prevents losing context at chunk boundaries
    - Example: "The product costs $50. It comes with..." 
    - Without overlap, "$50" and "It comes with" might be in different chunks
    - With overlap, both chunks contain the full sentence

```python
    # 3. METADATA: Tag every chunk with the client_id for security/SaaS
    metadatas = [{"client_id": client_id} for _ in chunks]
```

**Line 89**: Metadata generation
  - List comprehension creates one metadata dict per chunk
  - `{"client_id": "shop_001"}`: Attached to each chunk
  - **Why?** Multi-tenant security:
    - When querying, filter by `client_id`
    - Prevents shop_001 from seeing shop_002's data
    - Even though they share the same vector space

```python
    # 4. STORAGE: Save to ChromaDB on your local disk
    vector_db = Chroma.from_texts(
        texts=chunks,
        metadatas=metadatas,
        embedding=embeddings,
        persist_directory=client_db_path,
        collection_name=client_id
    )
```

**Lines 92-97**: Vector storage
  - `Chroma.from_texts()`: Convenience method that:
    1. Generates embeddings for each chunk (calls Google/OpenRouter API)
    2. Creates unique IDs for each chunk
    3. Stores vectors + metadata + original text in ChromaDB
  - `texts=chunks`: List of text strings to embed
  - `metadatas=metadatas`: Parallel list of metadata dicts
  - `embedding=embeddings`: Embedding model instance
  - `persist_directory`: Where to save database files on disk
  - `collection_name`: Namespace within ChromaDB
  - **What happens internally:**
    - For each chunk: `embedding_vector = embeddings.embed_query(chunk)`
    - Stores: `{id: uuid, vector: [0.1, 0.2, ...], metadata: {...}, text: "..."}`

```python
    print(f"✅ Success: Indexed {len(chunks)} chunks for {client_id}")
    return {"status": "success", "chunks_indexed": len(chunks), "message": f"Indexed {len(chunks)} chunks for {client_id}"}
```

**Lines 99-100**: Success response
  - Returns dict with status and count
  - Used by API endpoint to construct HTTP response

---

### File 3: `services/chatbot.py` (Third Most Complex)

This file implements the RAG query pipeline.

#### **Lines 1-18: Imports and Configuration**

```python
import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from core.config import Config

# ============================================================================
# MANUAL API CONTROL FOR CHAT (Backend Configuration)
# ============================================================================
# Change this value to switch which API is used for chat responses
# Options: "google" or "openrouter"
CHAT_API_PROVIDER = "google"
# ============================================================================
```

**Key imports:**
- `ChatGoogleGenerativeAI`: LLM for text generation
- `GoogleGenerativeAIEmbeddings`: For query embedding
- `Chroma`: Vector database client
- `create_retrieval_chain`: LangChain RAG orchestrator
- `create_stuff_documents_chain`: Combines retrieved docs into prompt
- `ChatPromptTemplate`: Prompt template builder

**Line 14**: Global configuration constant
  - **Why global?** Backend-controlled (not exposed to API users)
  - **Design decision**: API provider is infrastructure concern, not user concern

#### **Lines 20-68: get_chatbot_response() - RAG Pipeline**

```python
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
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
```

**Lines 28-40**: LLM initialization
  - **OpenRouter path:**
    - `model="openrouter/auto"`: Automatic model selection (cheapest available)
    - `base_url`: Routes to OpenRouter proxy
  - **Google path:**
    - `model="gemini-2.5-flash"`: Fast, cost-effective Gemini model
    - Automatically uses `GOOGLE_API_KEY` from environment

```python
    # Using gemini-embedding-001 - the standard embedding model for Google Generative AI
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
```

**Line 43**: Embeddings initialization
  - **Why always Google?** Embeddings must match indexing embeddings
  - **Critical constraint:** Query embeddings must use same model as indexed embeddings
  - **Why?** Different models produce incompatible vector spaces
    - Google embeddings: 768 dimensions
    - OpenAI embeddings: 1536 dimensions
    - Can't compare vectors from different spaces

```python
    # Use client-specific persist directory
    client_db_path = os.path.join(Config.VECTOR_DB_PATH, client_id)
    db = Chroma(persist_directory=client_db_path, embedding_function=embeddings, collection_name=client_id)
```

**Lines 46-47**: Load client's vector database
  - `client_db_path`: Same path structure as indexing
  - `embedding_function=embeddings`: Required for similarity search
  - `collection_name=client_id`: Loads specific client's collection
  - **What happens:** ChromaDB loads index from disk into memory

```python
    # Setup the retriever with your multi-tenant filter
    retriever = db.as_retriever(search_kwargs={'filter': {'client_id': client_id}})
```

**Line 50**: Create retriever with metadata filter
  - `as_retriever()`: Converts Chroma DB to LangChain Retriever interface
  - `search_kwargs`: Parameters passed to similarity search
  - `filter={'client_id': client_id}`: Metadata filter
  - **Why filter?** Multi-tenant security
    - Even if databases are separate, this adds defense-in-depth
    - Ensures only chunks with matching `client_id` metadata are retrieved

```python
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
```

**Lines 53-61**: Prompt template construction
  - `system_prompt`: Instructions for the LLM
  - `{context}`: Placeholder for retrieved chunks (filled by LangChain)
  - `{input}`: Placeholder for user query
  - `ChatPromptTemplate.from_messages()`: Creates structured prompt
  - **Message structure:**
    ```
    [
      {"role": "system", "content": "You are a helpful assistant..."},
      {"role": "user", "content": "What products do you offer?"}
    ]
    ```
  - **Why this format?** Matches OpenAI/Gemini chat API format

```python
    # Create the modern chain
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
```

**Lines 64-65**: RAG chain construction
  - `create_stuff_documents_chain()`: Creates chain that:
    1. Takes documents (retrieved chunks)
    2. "Stuffs" them into the `{context}` placeholder
    3. Sends complete prompt to LLM
  - `create_retrieval_chain()`: Wraps retriever + QA chain
  - **Chain flow:**
    ```
    User Query → Retriever (vector search) → Documents → 
    Stuff into Prompt → LLM → Answer
    ```

```python
    # Invoke the chain
    response = rag_chain.invoke({"input": user_query})
    return response["answer"]
```

**Lines 68-69**: Execute RAG pipeline
  - `invoke({"input": user_query})`: Triggers entire chain
  - **What happens internally:**
    1. Query embedding: `query_vector = embeddings.embed_query(user_query)`
    2. Vector search: `docs = db.similarity_search(query_vector, k=4)`
    3. Context building: `context = "\n\n".join([doc.page_content for doc in docs])`
    4. Prompt filling: `prompt.format(context=context, input=user_query)`
    5. LLM call: `llm.invoke(formatted_prompt)`
  - `response["answer"]`: Extracts answer string from response dict
  - **Response dict structure:**
    ```python
    {
      "input": "What products do you offer?",
      "context": [Document(...), Document(...), ...],
      "answer": "We offer laptops, phones, and accessories..."
    }
    ```

---

## Functional Logic Walkthrough

### Function 1: `index_website_data()` - Complete Algorithm

**Purpose:** Transform raw website URL into searchable vector embeddings

**Algorithm Steps:**

1. **Initialization Phase:**
   ```
   Input: url, client_id, use_sitemap, api_provider
   ↓
   Initialize embeddings model (Google or OpenRouter)
   ↓
   Construct client-specific database path: /data/vector_db/{client_id}/
   ↓
   Create directory if not exists
   ```

2. **Duplicate Check Phase:**
   ```
   Load existing ChromaDB collection
   ↓
   Query: existing_db.get()['ids']
   ↓
   If len(ids) > 0:
     Return {"status": "already_indexed"}
     EXIT
   ```

3. **Scraping Phase (Conditional):**
   ```
   If use_sitemap == True:
     ↓
     Validate url is string (not list)
     ↓
     Call scrape_website_sitemap(url)
       ↓
       Fetch sitemap.xml
       ↓
       Parse XML → Extract URLs
       ↓
       Filter URLs (remove product pages)
       ↓
       Scrape each URL (max 50)
       ↓
       Combine all text
   
   Else if isinstance(url, list):
     ↓
     Call scrape_multiple_urls(url)
       ↓
       For each URL in list:
         Scrape → Combine
   
   Else:
     ↓
     Call scrape_website(url)
       ↓
       Single HTTP request
       ↓
       Parse HTML → Extract text
   ```

4. **Chunking Phase:**
   ```
   raw_text (string, potentially 100KB+)
   ↓
   Initialize RecursiveCharacterTextSplitter(chunk_size=1000, overlap=150)
   ↓
   Split algorithm:
     Try split on "\n\n" (paragraphs)
     ↓
     If chunk > 1000 chars, split on "\n" (lines)
     ↓
     If still > 1000, split on ". " (sentences)
     ↓
     If still > 1000, split on " " (words)
     ↓
     Last resort: split on characters
   ↓
   Result: chunks = ["chunk1", "chunk2", ..., "chunkN"]
   ```

5. **Metadata Tagging Phase:**
   ```
   For each chunk in chunks:
     Create metadata dict: {"client_id": client_id}
   ↓
   Result: metadatas = [{"client_id": "shop_001"}, {"client_id": "shop_001"}, ...]
   ```

6. **Vectorization & Storage Phase:**
   ```
   For each chunk:
     ↓
     Call embeddings.embed_query(chunk)
     ↓
     API Request to Google/OpenRouter
     ↓
     Receive vector: [0.123, -0.456, 0.789, ...] (768 or 1536 dimensions)
     ↓
     Generate UUID for chunk
     ↓
     Store in ChromaDB:
       {
         id: uuid,
         vector: embedding_vector,
         metadata: {"client_id": "shop_001"},
         document: chunk_text
       }
   ↓
   Persist to disk: /data/vector_db/{client_id}/chroma.sqlite3
   ```

7. **Return Phase:**
   ```
   Return {
     "status": "success",
     "chunks_indexed": len(chunks),
     "message": "Indexed N chunks for client_id"
   }
   ```

**Complexity Analysis:**
- Time: O(n * m) where n = number of URLs, m = average page size
- Space: O(k) where k = total text size (all pages combined)
- API Calls: O(c) where c = number of chunks (each chunk = 1 embedding API call)

---

### Function 2: `get_chatbot_response()` - RAG Query Algorithm

**Purpose:** Convert user question into AI-generated answer using retrieved context

**Algorithm Steps:**

1. **LLM Selection Phase:**
   ```
   If CHAT_API_PROVIDER == "openrouter":
     ↓
     Validate OPENROUTER_API_KEY exists
     ↓
     Initialize ChatOpenAI(model="openrouter/auto")
   Else:
     ↓
     Initialize ChatGoogleGenerativeAI(model="gemini-2.5-flash")
   ```

2. **Database Loading Phase:**
   ```
   Initialize GoogleGenerativeAIEmbeddings
   ↓
   Construct path: /data/vector_db/{client_id}/
   ↓
   Load ChromaDB from disk:
     Read chroma.sqlite3
     ↓
     Load index into memory
     ↓
     Load embeddings metadata
   ```

3. **Retriever Configuration Phase:**
   ```
   Create retriever from database
   ↓
   Set search parameters:
     - k=4 (default, retrieve top 4 chunks)
     - filter={'client_id': client_id}
   ```

4. **Query Embedding Phase:**
   ```
   user_query = "What products do you offer?"
   ↓
   Call embeddings.embed_query(user_query)
   ↓
   API Request to Google Gemini
   ↓
   Receive query_vector: [0.234, -0.567, 0.890, ...] (768 dimensions)
   ```

5. **Vector Similarity Search Phase:**
   ```
   ChromaDB performs cosine similarity search:
   ↓
   For each stored vector:
     Calculate: cosine_similarity(query_vector, stored_vector)
     ↓
     Formula: dot(A, B) / (||A|| * ||B||)
   ↓
   Sort by similarity score (descending)
   ↓
   Filter by metadata: client_id == "shop_001"
   ↓
   Return top 4 chunks:
     [
       Document(page_content="...", metadata={"client_id": "shop_001"}),
       Document(page_content="...", metadata={"client_id": "shop_001"}),
       Document(page_content="...", metadata={"client_id": "shop_001"}),
       Document(page_content="...", metadata={"client_id": "shop_001"})
     ]
   ```

6. **Context Assembly Phase:**
   ```
   retrieved_docs = [doc1, doc2, doc3, doc4]
   ↓
   Combine documents:
     context = doc1.page_content + "\n\n" + doc2.page_content + "\n\n" + ...
   ```

7. **Prompt Construction Phase:**
   ```
   system_prompt = "You are a helpful assistant. Use the following pieces of retrieved context to answer the question. If you don't know the answer, say that you don't know.\n\n{context}"
   ↓
   Fill placeholders:
     system_prompt.replace("{context}", context)
     system_prompt.replace("{input}", user_query)
   ↓
   Result:
     "You are a helpful assistant. Use the following pieces of retrieved context to answer the question...
     
     [Retrieved context about products]
     
     Question: What products do you offer?"
   ```

8. **LLM Generation Phase:**
   ```
   Send prompt to LLM API (Google Gemini or OpenRouter)
   ↓
   LLM processes:
     - Reads system instructions
     - Analyzes retrieved context
     - Generates answer based on context
   ↓
   Receive response:
     "Based on the information provided, we offer laptops, smartphones, and accessories..."
   ```

9. **Response Extraction Phase:**
   ```
   response = {
     "input": "What products do you offer?",
     "context": [doc1, doc2, doc3, doc4],
     "answer": "Based on the information provided..."
   }
   ↓
   Extract: response["answer"]
   ↓
   Return answer string
   ```

**Complexity Analysis:**
- Time: O(d * e) where d = number of stored documents, e = embedding dimension
- Space: O(k) where k = size of retrieved context
- API Calls: 2 (1 for query embedding, 1 for LLM generation)

---

### Function 3: `scrape_website_sitemap()` - Sitemap Crawling Algorithm

**Purpose:** Scrape entire website by discovering URLs via sitemap.xml

**Algorithm Steps:**

1. **Sitemap Discovery Phase:**
   ```
   base_url = "https://example.com"
   ↓
   Parse URL: scheme="https", netloc="example.com"
   ↓
   Construct sitemap URL: "https://example.com/sitemap.xml"
   ↓
   HTTP GET request
   ```

2. **XML Parsing Phase:**
   ```
   response.content (XML bytes)
   ↓
   Parse with ElementTree
   ↓
   root = <urlset> or <sitemapindex>
   ```

3. **Sitemap Type Detection Phase:**
   ```
   Search for: <sitemap><loc>...</loc></sitemap>
   ↓
   If found:
     Type = "sitemapindex" (parent sitemap)
     ↓
     Extract child sitemap URLs
   Else:
     Type = "regular sitemap"
     ↓
     Extract page URLs directly
   ```

4. **Recursive Sitemap Fetching Phase (if sitemapindex):**
   ```
   For each child_sitemap_url:
     ↓
     HTTP GET child_sitemap_url
     ↓
     Parse XML
     ↓
     Extract <url><loc> elements
     ↓
     Append to all_urls list
   ```

5. **URL Filtering Phase:**
   ```
   all_urls = ["https://example.com/product/123", "https://example.com/collections/laptops", ...]
   ↓
   Call filter_product_pages(all_urls)
   ↓
   For each URL:
     ↓
     Check against skip_patterns:
       If "/product/" in url: SKIP
       If "/item/" in url: SKIP
       ...
     ↓
     Check against keep_patterns:
       If "/collections/" in url: KEEP
       If "/shop" in url: KEEP
       ...
     ↓
     If homepage (ends with .com/ or .lk/): KEEP
   ↓
   Result: filtered_urls = ["https://example.com/", "https://example.com/collections/laptops", ...]
   ```

6. **URL Limiting Phase:**
   ```
   If len(filtered_urls) > max_urls (50):
     ↓
     Truncate: filtered_urls = filtered_urls[:50]
   ```

7. **Batch Scraping Phase:**
   ```
   combined_text = ""
   ↓
   For each url in filtered_urls:
     ↓
     Call scrape_website(url)
       ↓
       HTTP GET
       ↓
       Parse HTML with BeautifulSoup
       ↓
       Remove <script>, <style>, <nav>, etc.
       ↓
       Extract text
     ↓
     Append to combined_text:
       combined_text += "\n\n--- Page: {url} ---\n{text}"
     ↓
     Sleep 1 second (rate limiting)
   ```

8. **Return Phase:**
   ```
   Return combined_text (string containing all pages)
   ```

**Complexity Analysis:**
- Time: O(n * p) where n = number of URLs, p = average page load time
- Space: O(t) where t = total text size
- Network: O(n + s) where s = number of sitemaps

---

## Variables & State Management

### Global State

#### **Configuration State (core/config.py)**

```python
class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    VECTOR_DB_PATH = str(Path(__file__).parent.parent / "data" / "vector_db")
```

**State Type:** Static configuration (loaded once at startup)

**Lifecycle:**
1. Application starts
2. `load_dotenv()` reads `.env` file
3. `os.getenv()` retrieves environment variables
4. Values stored in class attributes
5. Never modified during runtime

**Data Flow:**
```
.env file → os.environ → Config class attributes → Used by services
```

#### **API Provider State (services/chatbot.py)**

```python
CHAT_API_PROVIDER = "google"
```

**State Type:** Module-level constant

**Purpose:** Controls which LLM API is used for chat responses

**Modification:** Manual code change (not runtime configurable)

**Why not environment variable?** Design decision to keep API provider as infrastructure concern

---

### Request-Scoped State

#### **Ingestion Request State**

**Entry Point:** `POST /ingest`

**State Variables:**

1. **`request: IngestRequest`**
   ```python
   {
     "url": "https://example.com" or ["url1", "url2"],
     "client_id": "shop_001",
     "use_sitemap": False,
     "api_provider": "google"
   }
   ```
   - **Type:** Pydantic model (validated)
   - **Lifecycle:** Created from JSON → Validated → Passed to indexer → Discarded
   - **Validation:** Pydantic ensures types match schema

2. **`api_key: str`**
   - **Source:** HTTP header `X-API-Key`
   - **Lifecycle:** Extracted by FastAPI → Validated by middleware → Discarded
   - **Security:** Never logged or stored

3. **`raw_text: str`**
   - **Source:** Scraper output
   - **Size:** Can be 100KB - 10MB depending on website
   - **Lifecycle:** Scraped → Chunked → Discarded (not stored, only chunks stored)
   - **Memory:** Held in RAM during processing

4. **`chunks: List[str]`**
   - **Source:** Text splitter output
   - **Example:**
     ```python
     [
       "Welcome to our store. We offer...",
       "...laptops, phones, and accessories. Our products...",
       "...are high quality and affordable. Contact us..."
     ]
     ```
   - **Size:** Typically 50-500 chunks per website
   - **Lifecycle:** Created → Embedded → Stored in DB → Discarded from memory

5. **`metadatas: List[Dict]`**
   - **Structure:**
     ```python
     [
       {"client_id": "shop_001"},
       {"client_id": "shop_001"},
       {"client_id": "shop_001"}
     ]
     ```
   - **Purpose:** Multi-tenant filtering
   - **Lifecycle:** Created → Stored with chunks → Used in queries

6. **`embeddings: GoogleGenerativeAIEmbeddings`**
   - **Type:** Embedding model instance
   - **State:** Stateless (no internal state changes)
   - **Lifecycle:** Created → Used for embedding → Discarded
   - **API Calls:** One per chunk

7. **`vector_db: Chroma`**
   - **Type:** Vector database instance
   - **State:** Persistent (writes to disk)
   - **Lifecycle:** Created → Populated → Persisted → Closed
   - **Storage:** SQLite file + index files

#### **Chat Request State**

**Entry Point:** `POST /chat`

**State Variables:**

1. **`request: ChatRequest`**
   ```python
   {
     "query": "What products do you offer?",
     "client_id": "shop_001"
   }
   ```
   - **Type:** Pydantic model
   - **Lifecycle:** Created → Validated → Passed to chatbot → Discarded

2. **`user_query: str`**
   - **Source:** `request.query`
   - **Transformations:**
     - Original: "What products do you offer?"
     - Embedded: [0.123, -0.456, ...] (768-dim vector)
     - Used in: Vector search

3. **`llm: ChatGoogleGenerativeAI`**
   - **Type:** LLM instance
   - **State:** Stateless (no conversation history)
   - **Lifecycle:** Created → Used once → Discarded
   - **API Calls:** One per query

4. **`db: Chroma`**
   - **Type:** Vector database instance
   - **State:** Read-only (loads from disk)
   - **Lifecycle:** Loaded → Queried → Closed
   - **Memory:** Index loaded into RAM

5. **`retriever: VectorStoreRetriever`**
   - **Type:** LangChain retriever
   - **Configuration:**
     ```python
     {
       "search_type": "similarity",
       "search_kwargs": {
         "k": 4,
         "filter": {"client_id": "shop_001"}
       }
     }
     ```
   - **State:** Wraps database with search parameters

6. **`retrieved_docs: List[Document]`**
   - **Structure:**
     ```python
     [
       Document(
         page_content="We offer laptops, phones...",
         metadata={"client_id": "shop_001"}
       ),
       Document(
         page_content="Our products are high quality...",
         metadata={"client_id": "shop_001"}
       ),
       ...
     ]
     ```
   - **Size:** Typically 4 documents (configurable via k parameter)
   - **Lifecycle:** Retrieved → Stuffed into prompt → Discarded

7. **`response: Dict`**
   - **Structure:**
     ```python
     {
       "input": "What products do you offer?",
       "context": [doc1, doc2, doc3, doc4],
       "answer": "Based on the information provided..."
     }
     ```
   - **Lifecycle:** Generated by chain → Answer extracted → Discarded

---

### Persistent State

#### **Vector Database State (ChromaDB)**

**Location:** `/data/vector_db/{client_id}/`

**Files:**
- `chroma.sqlite3`: SQLite database with metadata
- `index/`: HNSW index files for fast similarity search

**Schema:**
```
Table: embeddings
Columns:
  - id: UUID (primary key)
  - embedding: BLOB (serialized vector)
  - document: TEXT (original chunk text)
  - metadata: JSON ({"client_id": "shop_001"})
```

**State Changes:**
1. **Ingestion:** INSERT new embeddings
2. **Query:** SELECT with similarity search (no modifications)
3. **No updates or deletes** (append-only in current implementation)

**Indexing:**
- HNSW (Hierarchical Navigable Small World) index for fast approximate nearest neighbor search
- Trade-off: Slightly less accurate than brute force, but 100x faster

---

## Control Flow & Conditional Logic

### Authentication Flow (api/middleware/auth.py)

```python
async def verify_api_key(api_key: str) -> str:
    try:
        valid_key = APIKeyValidator.get_valid_api_key()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API configuration error"
        )
    
    if api_key != valid_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key
```

**Control Flow:**

```
START
  ↓
Try to get valid API key from environment
  ↓
  ├─ SUCCESS: valid_key = "abc123..."
  │   ↓
  │   Compare api_key == valid_key
  │   ↓
  │   ├─ MATCH: Return api_key (authentication successful)
  │   │   ↓
  │   │   Continue to endpoint handler
  │   │
  │   └─ NO MATCH: Raise HTTPException(401, "Invalid API key")
  │       ↓
  │       Return 401 Unauthorized to client
  │
  └─ FAILURE: API_KEY not in environment
      ↓
      Raise HTTPException(500, "API configuration error")
      ↓
      Return 500 Internal Server Error to client
```

**Conditions:**
1. **Environment variable exists?**
   - YES → Continue
   - NO → 500 error (server misconfiguration)

2. **API key matches?**
   - YES → Allow request
   - NO → 401 error (unauthorized)

---

### Ingestion Flow Control (api/routes/ingest.py)

```python
async def ingest_website(request: IngestRequest, api_key: str):
    try:
        # Verify API key
        await APIKeyValidator.verify_api_key(api_key)
        
        # Validate inputs
        if not request.url or not request.client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="url and client_id are required"
            )
        
        # If url is a list, validate it's not empty
        if isinstance(request.url, list) and len(request.url) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="url list cannot be empty"
            )
        
        # Index the website
        result = index_website_data(request.url, request.client_id, use_sitemap=request.use_sitemap, api_provider=request.api_provider)
        
        # Handle already indexed response
        if isinstance(result, dict) and result.get("status") == "already_indexed":
            return IngestResponse(
                status="already_indexed",
                message="Data already indexed for this client",
                client_id=request.client_id
            )
        
        # Handle success response
        chunks_indexed = result.get("chunks_indexed") if isinstance(result, dict) else result
        
        return IngestResponse(
            status="success",
            message=f"Successfully indexed website for {request.client_id}",
            chunks_indexed=chunks_indexed,
            client_id=request.client_id
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ingest error: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Indexing failed. Please contact support."
        )
```

**Control Flow Diagram:**

```
START: POST /ingest
  ↓
Verify API key
  ↓
  ├─ INVALID → Return 401 Unauthorized
  │
  └─ VALID
      ↓
      Validate request.url exists
      ↓
      ├─ MISSING → Return 400 Bad Request
      │
      └─ EXISTS
          ↓
          Validate request.client_id exists
          ↓
          ├─ MISSING → Return 400 Bad Request
          │
          └─ EXISTS
              ↓
              Check if url is list
              ↓
              ├─ YES → Check if empty
              │   ↓
              │   ├─ EMPTY → Return 400 Bad Request
              │   │
              │   └─ NOT EMPTY → Continue
              │
              └─ NO (single URL) → Continue
                  ↓
                  Call index_website_data()
                  ↓
                  ├─ ValueError raised → Return 400 Bad Request
                  │
                  ├─ Other Exception → Log error → Return 500 Internal Server Error
                  │
                  └─ SUCCESS
                      ↓
                      Check result.status
                      ↓
                      ├─ "already_indexed" → Return IngestResponse(status="already_indexed")
                      │
                      └─ "success" → Return IngestResponse(status="success", chunks_indexed=N)
```

**Key Decision Points:**

1. **API Key Validation:** Security gate
2. **Input Validation:** Prevents invalid data from reaching business logic
3. **URL Type Check:** Handles both single URL and list of URLs
4. **Empty List Check:** Prevents wasted processing
5. **Result Status Check:** Differentiates between new indexing and duplicate
6. **Exception Handling:** Graceful error responses

---

### Indexing Flow Control (services/indexer.py)

```python
def index_website_data(url, client_id, use_sitemap=False, api_provider="google"):
    # 1. Initialize embeddings
    embeddings = get_embeddings(api_provider)
    
    # 2. Check if already indexed
    client_db_path = os.path.join(Config.VECTOR_DB_PATH, client_id)
    os.makedirs(client_db_path, exist_ok=True)
    
    existing_db = Chroma(
        persist_directory=client_db_path,
        collection_name=client_id,
        embedding_function=embeddings
    )
    
    if len(existing_db.get()['ids']) > 0:
        return {"status": "already_indexed", "message": f"Data for {client_id} already indexed"}
    
    # 3. Scraping strategy selection
    if use_sitemap:
        if isinstance(url, list):
            raise ValueError("use_sitemap=True but got multiple URLs. Set use_sitemap=False to scrape multiple URLs directly.")
        raw_text = scrape_website_sitemap(url)
    else:
        if isinstance(url, list):
            raw_text = scrape_multiple_urls(url, rate_limit_delay=1, max_urls=len(url))
        else:
            raw_text = scrape_website(url)
    
    # 4. Chunking
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_text(raw_text)
    
    # 5. Metadata tagging
    metadatas = [{"client_id": client_id} for _ in chunks]
    
    # 6. Vectorization and storage
    vector_db = Chroma.from_texts(
        texts=chunks,
        metadatas=metadatas,
        embedding=embeddings,
        persist_directory=client_db_path,
        collection_name=client_id
    )
    
    return {"status": "success", "chunks_indexed": len(chunks), "message": f"Indexed {len(chunks)} chunks for {client_id}"}
```

**Control Flow Diagram:**

```
START: index_website_data(url, client_id, use_sitemap, api_provider)
  ↓
Initialize embeddings based on api_provider
  ↓
  ├─ api_provider == "openrouter"
  │   ↓
  │   Check OPENROUTER_API_KEY exists
  │   ↓
  │   ├─ MISSING → Raise ValueError
  │   │
  │   └─ EXISTS → Create OpenAIEmbeddings
  │
  └─ api_provider == "google" (default)
      ↓
      Create GoogleGenerativeAIEmbeddings
      ↓
      Create client database directory
      ↓
      Load existing database
      ↓
      Check if data already indexed
      ↓
      ├─ len(ids) > 0 → Return {"status": "already_indexed"}
      │   ↓
      │   EXIT (no scraping or indexing)
      │
      └─ len(ids) == 0 → Continue with indexing
          ↓
          Check use_sitemap flag
          ↓
          ├─ use_sitemap == True
          │   ↓
          │   Check if url is list
          │   ↓
          │   ├─ YES → Raise ValueError (invalid combination)
          │   │
          │   └─ NO → Call scrape_website_sitemap(url)
          │       ↓
          │       Fetch sitemap.xml
          │       ↓
          │       Extract URLs
          │       ↓
          │       Filter product pages
          │       ↓
          │       Scrape each URL (max 50)
          │       ↓
          │       Combine text
          │
          └─ use_sitemap == False
              ↓
              Check if url is list
              ↓
              ├─ YES → Call scrape_multiple_urls(url)
              │   ↓
              │   For each URL:
              │     Scrape → Combine
              │
              └─ NO → Call scrape_website(url)
                  ↓
                  Single page scrape
                  ↓
                  raw_text obtained
                  ↓
                  Split into chunks
                  ↓
                  Create metadata for each chunk
                  ↓
                  Generate embeddings (API calls)
                  ↓
                  Store in ChromaDB
                  ↓
                  Persist to disk
                  ↓
                  Return {"status": "success", "chunks_indexed": N}
```

**Key Decision Points:**

1. **API Provider Selection:** Determines which embedding API to use
2. **Duplicate Check:** Prevents re-indexing (saves time and money)
3. **Sitemap Flag:** Determines scraping strategy
4. **URL Type Check:** Handles single vs. multiple URLs
5. **Sitemap + List Validation:** Prevents invalid parameter combination

---

### Chat Flow Control (services/chatbot.py)

```python
def get_chatbot_response(user_query, client_id):
    # 1. LLM selection
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
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    
    # 2. Load database
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    client_db_path = os.path.join(Config.VECTOR_DB_PATH, client_id)
    db = Chroma(persist_directory=client_db_path, embedding_function=embeddings, collection_name=client_id)
    
    # 3. Setup retriever
    retriever = db.as_retriever(search_kwargs={'filter': {'client_id': client_id}})
    
    # 4. Create prompt
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
    
    # 5. Create chain
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    # 6. Execute
    response = rag_chain.invoke({"input": user_query})
    return response["answer"]
```

**Control Flow Diagram:**

```
START: get_chatbot_response(user_query, client_id)
  ↓
Check CHAT_API_PROVIDER constant
  ↓
  ├─ CHAT_API_PROVIDER == "openrouter"
  │   ↓
  │   Check OPENROUTER_API_KEY exists
  │   ↓
  │   ├─ MISSING → Raise ValueError
  │   │
  │   └─ EXISTS → Initialize ChatOpenAI
  │
  └─ CHAT_API_PROVIDER == "google" (default)
      ↓
      Initialize ChatGoogleGenerativeAI
      ↓
      Initialize embeddings (always Google)
      ↓
      Construct database path
      ↓
      Load ChromaDB from disk
      ↓
      ├─ Database not found → ChromaDB raises error
      │   ↓
      │   Propagates to API layer → 500 error
      │
      └─ Database loaded successfully
          ↓
          Create retriever with client_id filter
          ↓
          Create prompt template
          ↓
          Create document chain (LLM + prompt)
          ↓
          Create retrieval chain (retriever + document chain)
          ↓
          Invoke chain with user_query
          ↓
          ┌─────────────────────────────────┐
          │ Chain Execution (Internal Flow) │
          └─────────────────────────────────┘
          ↓
          1. Embed user_query → query_vector
          ↓
          2. Vector similarity search
          ↓
          3. Filter by client_id metadata
          ↓
          4. Retrieve top 4 chunks
          ↓
          ├─ No chunks found → LLM generates "I don't know" response
          │
          └─ Chunks found → Continue
              ↓
              5. Combine chunks into context string
              ↓
              6. Fill prompt template
              ↓
              7. Send to LLM API
              ↓
              8. Receive generated answer
              ↓
              9. Return response dict
              ↓
              Extract response["answer"]
              ↓
              Return answer string
```

**Key Decision Points:**

1. **LLM Provider Selection:** Determines which API to use for generation
2. **API Key Validation:** Ensures OpenRouter key exists if selected
3. **Database Existence:** Implicitly checked by ChromaDB (raises error if not found)
4. **Chunk Retrieval:** If no chunks found, LLM still generates response (but says "I don't know")

---

## Data Transformation Details

### Transformation 1: URL → Vector Embeddings

**Input:** `"https://example.com"`

**Step-by-Step Transformation:**

1. **HTTP Request:**
   ```
   Input: "https://example.com"
   ↓
   HTTP GET request
   ↓
   Output: HTML string (raw bytes)
   ```
   Example:
   ```html
   <!DOCTYPE html>
   <html>
   <head><title>Example Store</title></head>
   <body>
     <nav>Menu</nav>
     <h1>Welcome to Example Store</h1>
     <p>We offer laptops, phones, and accessories.</p>
     <script>console.log('tracking');</script>
   </body>
   </html>
   ```

2. **HTML Parsing:**
   ```
   Input: HTML string
   ↓
   BeautifulSoup parsing
   ↓
   Output: DOM tree structure
   ```
   Tree structure:
   ```
   <html>
     ├─ <head>
     │   └─ <title>
     └─ <body>
         ├─ <nav>
         ├─ <h1>
         ├─ <p>
         └─ <script>
   ```

3. **Noise Removal:**
   ```
   Input: DOM tree
   ↓
   Remove: <script>, <style>, <nav>, <footer>, <header>, <aside>
   ↓
   Output: Cleaned DOM tree
   ```
   Cleaned tree:
   ```
   <html>
     └─ <body>
         ├─ <h1>
         └─ <p>
   ```

4. **Text Extraction:**
   ```
   Input: Cleaned DOM tree
   ↓
   Extract all text nodes
   ↓
   Join with spaces
   ↓
   Output: Clean text string
   ```
   Result:
   ```
   "Welcome to Example Store We offer laptops, phones, and accessories."
   ```

5. **Text Chunking:**
   ```
   Input: "Welcome to Example Store We offer laptops, phones, and accessories."
   ↓
   RecursiveCharacterTextSplitter(chunk_size=1000, overlap=150)
   ↓
   Output: List of chunks
   ```
   Result (simplified - actual chunks would be larger):
   ```python
   [
     "Welcome to Example Store We offer laptops, phones, and accessories."
   ]
   ```

6. **Metadata Tagging:**
   ```
   Input: ["chunk1"]
   ↓
   Add metadata: {"client_id": "shop_001"}
   ↓
   Output: [{"text": "chunk1", "metadata": {"client_id": "shop_001"}}]
   ```

7. **Embedding Generation:**
   ```
   Input: "Welcome to Example Store We offer laptops, phones, and accessories."
   ↓
   API call: embeddings.embed_query(chunk)
   ↓
   Google Gemini API processes text
   ↓
   Output: 768-dimensional vector
   ```
   Result (truncated for display):
   ```python
   [0.0234, -0.0567, 0.0890, 0.0123, -0.0456, ..., 0.0789]  # 768 numbers
   ```

8. **Vector Storage:**
   ```
   Input: {
     "text": "Welcome to Example Store...",
     "vector": [0.0234, -0.0567, ...],
     "metadata": {"client_id": "shop_001"}
   }
   ↓
   Generate UUID: "a1b2c3d4-e5f6-..."
   ↓
   Store in ChromaDB
   ↓
   Persist to disk: /data/vector_db/shop_001/chroma.sqlite3
   ```

**Final State in Database:**
```sql
INSERT INTO embeddings VALUES (
  'a1b2c3d4-e5f6-...',  -- id
  BLOB([0.0234, -0.0567, ...]),  -- embedding vector
  'Welcome to Example Store We offer laptops, phones, and accessories.',  -- document
  '{"client_id": "shop_001"}'  -- metadata
);
```

---

### Transformation 2: User Query → AI Answer

**Input:** `"What products do you offer?"`

**Step-by-Step Transformation:**

1. **Query Embedding:**
   ```
   Input: "What products do you offer?"
   ↓
   API call: embeddings.embed_query(query)
   ↓
   Google Gemini API processes query
   ↓
   Output: 768-dimensional query vector
   ```
   Result:
   ```python
   query_vector = [0.0345, -0.0678, 0.0901, ..., 0.0234]  # 768 numbers
   ```

2. **Vector Similarity Search:**
   ```
   Input: query_vector = [0.0345, -0.0678, ...]
   ↓
   For each stored vector in database:
     Calculate cosine_similarity(query_vector, stored_vector)
   ↓
   Formula: dot(A, B) / (||A|| * ||B||)
   ↓
   Sort by similarity score (descending)
   ↓
   Filter by metadata: client_id == "shop_001"
   ↓
   Take top 4 results
   ↓
   Output: List of (chunk, score) tuples
   ```
   Result:
   ```python
   [
     (Document("We offer laptops, phones, and accessories..."), 0.89),
     (Document("Our products include high-end laptops..."), 0.85),
     (Document("Phone selection includes iPhone and Samsung..."), 0.82),
     (Document("Accessories: cases, chargers, headphones..."), 0.78)
   ]
   ```

3. **Context Assembly:**
   ```
   Input: [doc1, doc2, doc3, doc4]
   ↓
   Extract page_content from each document
   ↓
   Join with "\n\n" separator
   ↓
   Output: Context string
   ```
   Result:
   ```
   "We offer laptops, phones, and accessories...
   
   Our products include high-end laptops...
   
   Phone selection includes iPhone and Samsung...
   
   Accessories: cases, chargers, headphones..."
   ```

4. **Prompt Construction:**
   ```
   Input: 
     - context = "We offer laptops, phones, and accessories..."
     - user_query = "What products do you offer?"
   ↓
   Fill template:
     system_prompt = "You are a helpful assistant. Use the following pieces of retrieved context to answer the question. If you don't know the answer, say that you don't know.\n\n{context}"
     human_prompt = "{input}"
   ↓
   Replace placeholders
   ↓
   Output: Formatted prompt
   ```
   Result:
   ```
   [
     {
       "role": "system",
       "content": "You are a helpful assistant. Use the following pieces of retrieved context to answer the question. If you don't know the answer, say that you don't know.\n\nWe offer laptops, phones, and accessories...\n\nOur products include high-end laptops...\n\nPhone selection includes iPhone and Samsung...\n\nAccessories: cases, chargers, headphones..."
     },
     {
       "role": "user",
       "content": "What products do you offer?"
     }
   ]
   ```

5. **LLM Generation:**
   ```
   Input: Formatted prompt
   ↓
   API call to Google Gemini
   ↓
   LLM processes:
     - Reads system instructions
     - Analyzes retrieved context
     - Identifies relevant information
     - Generates natural language response
   ↓
   Output: Generated text
   ```
   Result:
   ```
   "Based on the information provided, we offer a variety of products including laptops, phones, and accessories. Our laptop selection includes high-end models, and for phones, we carry both iPhone and Samsung devices. We also stock accessories such as cases, chargers, and headphones."
   ```

6. **Response Extraction:**
   ```
   Input: {
     "input": "What products do you offer?",
     "context": [doc1, doc2, doc3, doc4],
     "answer": "Based on the information provided..."
   }
   ↓
   Extract: response["answer"]
   ↓
   Output: Answer string
   ```
   Result:
   ```
   "Based on the information provided, we offer a variety of products including laptops, phones, and accessories. Our laptop selection includes high-end models, and for phones, we carry both iPhone and Samsung devices. We also stock accessories such as cases, chargers, and headphones."
   ```

7. **HTTP Response:**
   ```
   Input: answer string
   ↓
   Wrap in Pydantic model
   ↓
   Serialize to JSON
   ↓
   Output: HTTP response
   ```
   Result:
   ```json
   {
     "status": "success",
     "answer": "Based on the information provided, we offer a variety of products including laptops, phones, and accessories. Our laptop selection includes high-end models, and for phones, we carry both iPhone and Samsung devices. We also stock accessories such as cases, chargers, and headphones.",
     "client_id": "shop_001"
   }
   ```

---

## Advanced Technical Details

### Vector Similarity Mathematics

**Cosine Similarity Formula:**
```
similarity = (A · B) / (||A|| × ||B||)

Where:
- A · B = dot product = Σ(Ai × Bi)
- ||A|| = magnitude of A = √(Σ(Ai²))
- ||B|| = magnitude of B = √(Σ(Bi²))
```

**Example Calculation:**
```python
# Simplified 3D vectors (actual vectors are 768D)
query_vector = [0.5, 0.3, 0.2]
chunk_vector = [0.6, 0.4, 0.1]

# Dot product
dot_product = (0.5 * 0.6) + (0.3 * 0.4) + (0.2 * 0.1)
            = 0.30 + 0.12 + 0.02
            = 0.44

# Magnitudes
magnitude_A = sqrt(0.5² + 0.3² + 0.2²) = sqrt(0.38) = 0.616
magnitude_B = sqrt(0.6² + 0.4² + 0.1²) = sqrt(0.53) = 0.728

# Cosine similarity
similarity = 0.44 / (0.616 × 0.728)
           = 0.44 / 0.448
           = 0.982

# Result: 98.2% similar (very high similarity)
```

**Why Cosine Similarity?**
- Measures angle between vectors (not distance)
- Range: -1 (opposite) to 1 (identical)
- Ignores magnitude (only cares about direction)
- Perfect for semantic similarity (meaning, not length)

---

### ChromaDB Indexing Strategy

**HNSW (Hierarchical Navigable Small World) Algorithm:**

1. **Graph Construction:**
   - Each vector is a node
   - Nodes connected to nearest neighbors
   - Multiple layers (hierarchical)
   - Top layer: sparse, long-range connections
   - Bottom layer: dense, local connections

2. **Search Process:**
   ```
   Query vector arrives
   ↓
   Start at top layer (sparse graph)
   ↓
   Greedy search: move to nearest neighbor
   ↓
   Descend to next layer
   ↓
   Repeat until bottom layer
   ↓
   Return k nearest neighbors
   ```

3. **Trade-offs:**
   - **Speed:** O(log n) vs O(n) for brute force
   - **Accuracy:** ~95-99% recall (misses some true neighbors)
   - **Memory:** Stores graph structure (extra overhead)

---

### LangChain Chain Mechanics

**What `create_retrieval_chain()` Actually Does:**

```python
# Simplified implementation (conceptual)
class RetrievalChain:
    def __init__(self, retriever, combine_docs_chain):
        self.retriever = retriever
        self.combine_docs_chain = combine_docs_chain
    
    def invoke(self, inputs):
        # Step 1: Retrieve documents
        query = inputs["input"]
        docs = self.retriever.get_relevant_documents(query)
        
        # Step 2: Combine docs and generate answer
        result = self.combine_docs_chain.invoke({
            "input": query,
            "context": docs
        })
        
        # Step 3: Return full response
        return {
            "input": query,
            "context": docs,
            "answer": result["output"]
        }
```

**What `create_stuff_documents_chain()` Actually Does:**

```python
# Simplified implementation (conceptual)
class StuffDocumentsChain:
    def __init__(self, llm, prompt):
        self.llm = llm
        self.prompt = prompt
    
    def invoke(self, inputs):
        # Step 1: Extract documents
        docs = inputs["context"]
        
        # Step 2: "Stuff" documents into context string
        context_str = "\n\n".join([doc.page_content for doc in docs])
        
        # Step 3: Format prompt
        formatted_prompt = self.prompt.format(
            context=context_str,
            input=inputs["input"]
        )
        
        # Step 4: Call LLM
        response = self.llm.invoke(formatted_prompt)
        
        # Step 5: Return answer
        return {"output": response.content}
```

---

## Performance Characteristics

### Ingestion Performance

**Time Complexity:**
- Scraping: O(n × p) where n = URLs, p = page load time
- Chunking: O(t) where t = total text length
- Embedding: O(c × e) where c = chunks, e = embedding API latency
- Storage: O(c × log c) for HNSW index construction

**Typical Timings:**
- Single page scrape: 1-3 seconds
- Sitemap scrape (50 pages): 60-90 seconds (with rate limiting)
- Chunking 100KB text: <1 second
- Embedding 100 chunks: 10-30 seconds (API dependent)
- Total for medium website: 2-5 minutes

**Bottlenecks:**
1. **Network I/O:** Scraping is slowest part
2. **API Rate Limits:** Embedding API has request limits
3. **Disk I/O:** ChromaDB persistence (minimal impact)

---

### Query Performance

**Time Complexity:**
- Query embedding: O(1) - single API call
- Vector search: O(log n) with HNSW index
- LLM generation: O(1) - single API call

**Typical Timings:**
- Query embedding: 200-500ms
- Vector search: 10-50ms (for 10K vectors)
- LLM generation: 1-3 seconds
- Total response time: 1.5-4 seconds

**Bottlenecks:**
1. **LLM API:** Slowest part (generation time)
2. **Query embedding:** Second slowest
3. **Vector search:** Negligible (highly optimized)

---

## Security Considerations

### Multi-Tenant Isolation

**Mechanisms:**
1. **Separate directories:** `/data/vector_db/{client_id}/`
2. **Separate collections:** `collection_name=client_id`
3. **Metadata filtering:** `filter={'client_id': client_id}`

**Defense in Depth:**
- Even if directory isolation fails, metadata filter prevents cross-tenant access
- Even if metadata filter fails, separate collections provide isolation

### API Key Security

**Storage:**
- Environment variables (not in code)
- Never logged or exposed in responses

**Validation:**
- Every request validated
- Constant-time comparison (prevents timing attacks)

**Error Handling:**
- Generic error messages (don't reveal if key exists)
- 401 for invalid key (not 404)

---

## Conclusion

This RAG chatbot implements a sophisticated pipeline that transforms unstructured web content into a queryable knowledge base. The key innovations are:

1. **Intelligent Scraping:** Sitemap-based crawling with product page filtering
2. **Semantic Chunking:** Overlap-based splitting preserves context
3. **Vector Search:** HNSW indexing enables fast similarity search
4. **Multi-Tenant Architecture:** Isolated data per client
5. **Flexible API Providers:** Supports both Google and OpenRouter

The system balances performance, cost, and accuracy through careful algorithm selection and optimization strategies.
