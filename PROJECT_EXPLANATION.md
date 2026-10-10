# 🚀 Multi-Tenant RAG Chatbot: Complete Project Technical Explanation & Interview Guide

> **Target Audience:** Engineering Candidates preparing for Technical Interviews (Internship / Junior Software Engineer / AI Engineer).  
> **Repository:** `chatbot-rag`  
> **Key Architecture:** Multi-Tenant Retrieval-Augmented Generation (RAG) platform with automated website crawling, vector database isolation, dual-provider LLM orchestration, and embeddable frontend widget.

---

## 📑 Table of Contents
1. [Executive Summary (The Elevator Pitch)](#1-executive-summary-the-elevator-pitch)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Deep-Dive: Multi-Client & Multi-Tenant Isolation](#3-deep-dive-multi-client--multi-tenant-isolation)
4. [Line-by-Line / Module-by-Module Codebase Walkthrough](#4-line-by-line--module-by-module-codebase-walkthrough)
   - [4.1 Backend Entry & Core Configuration](#41-backend-entry--core-configuration)
   - [4.2 Security & Authentication Layer](#42-security--authentication-layer)
   - [4.3 Ingestion & Web Scraping Pipeline](#43-ingestion--web-scraping-pipeline)
   - [4.4 Chunking, Embedding & Vector Storage](#44-chunking-embedding--vector-storage)
   - [4.5 Retrieval & Chatbot Intelligence Engine](#45-retrieval--chatbot-intelligence-engine)
   - [4.6 Embeddable Frontend Widget & Client Proxy Pattern](#46-embeddable-frontend-widget--client-proxy-pattern)
5. [Key Technical Decisions & Technology Stack Rationale](#5-key-technical-decisions--technology-stack-rationale)
   - [5.1 Why Each Core Technology Was Chosen](#51-why-each-core-technology-was-chosen)
     - Why FastAPI (vs. Flask / Django)
     - Why ChromaDB & SQLite 3 (chroma.sqlite3)
     - Why Google Gemini 2.5 Flash & Gemini Embeddings
     - Why LangChain (LCEL Orchestration)
     - Why Vanilla JavaScript UMD for Widget
     - Why Docker & Nginx
   - [5.2 Engineering Decisions & Trade-Offs Matrix](#52-engineering-decisions--trade-offs-matrix)
6. [Current System Limitations & Production Roadmap](#6-current-system-limitations--production-roadmap)
7. [Comprehensive Technical Interview Q&A (35+ Questions)](#7-comprehensive-technical-interview-qa)
   - [Category A: Multi-Tenancy & Data Isolation](#category-a-multi-tenancy--data-isolation)
   - [Category B: RAG, Embeddings & Vector Search](#category-b-rag-embeddings--vector-search)
   - [Category C: Scraping, Ingestion & Data Processing](#category-c-scraping-ingestion--data-processing)
   - [Category D: API Architecture, Security & Proxying](#category-d-api-architecture-security--proxying)
   - [Category E: System Design & Scaling to Production](#category-e-system-design--scaling-to-production)
   - [Category F: Real-World Gotchas & Debugging Scenarios](#category-f-real-world-gotchas--debugging-scenarios)
8. [Candidate Cheatsheet: 1-Minute Pitch & 5-Minute Technical Walkthrough](#8-candidate-cheatsheet-1-minute-pitch--5-minute-technical-walkthrough)

---

## 1. Executive Summary (The Elevator Pitch)

### What is this project?
The **Multi-Tenant RAG Chatbot Platform** is a full-stack, enterprise-style AI customer support engine. It allows multiple independent businesses (tenants/clients) to input their website URL (e.g., an e-commerce shop), automatically crawl and vectorize all textual and product knowledge, and embed a lightweight, branded chat widget onto their website. 

When visitors chat with the widget, the bot responds using **Retrieval-Augmented Generation (RAG)**—meaning it answers strictly using facts extracted from the client's website, accompanied by exact product links, while preventing cross-tenant data leakage.

### The Problem It Solves:
1. **Generic LLM Hallucinations:** Vanilla LLMs (like GPT-4 or Gemini) do not know inventory, store return policies, or real-time catalog prices of specific SMB websites.
2. **Expensive Model Fine-Tuning:** Fine-tuning an LLM on website text is prohibitively slow, costly, and impossible to update in real-time when stock or prices change.
3. **Multi-Tenant Data Privacy:** E-commerce stores cannot have their catalog, pricing, or internal content shared or retrieved by other stores on the same platform.
4. **Client-Side API Key Exposure:** Public frontend JavaScript widgets cannot carry backend API secrets without exposing them in browser devtools.

---

## 2. End-to-End System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT WEBSITE                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ <script src=".../rag-chat-widget.umd.js"></script>                    │  │
│  │ window.RAGChatBot = { apiUrl: "http://client-proxy:3000",             │  │
│  │                       clientId: "shop_001" };                         │  │
│  │                                                                       │  │
│  │  [💬 Chat Bubble] ───> [💬 Chat Window]                               │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
└──────────────────────────────────────┼──────────────────────────────────────┘
                                       │ 1. POST /chat { query, client_id }
                                       │    (No Secret API Key exposed)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CLIENT-SIDE BACKEND PROXY                             │
│                     (Node.js / Express / Python)                            │
│  Injects hidden RAG_API_KEY from server environment (.env)                  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 2. POST /chat
                                       │    Headers: { "X-API-Key": "sk_live_..." }
                                       │    Body: { "query": "...", "client_id": "shop_001" }
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND SERVICE                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 🔒 Auth Middleware (APIKeyValidator: X-API-Key Header Check)          │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      │ Passes Validation                    │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 🌐 Router: POST /ingest                  💬 Router: POST /chat        │  │
│  └───────────────────┬───────────────────────────────────┬───────────────┘  │
│                      │                                   │                  │
│                      ▼                                   ▼                  │
│  ┌───────────────────────────────┐   ┌───────────────────────────────────┐  │
│  │ INGESTION PIPELINE            │   │ QUERY & RAG PIPELINE              │  │
│  │ 1. scraper.py:                │   │ 1. Query Classifier:              │  │
│  │    - Fetch Sitemap / URL      │   │    - Store info vs Product vs Gen │  │
│  │    - Clean HTML (strip tags)  │   │ 2. Vector DB Retrieval:           │  │
│  │    - Extract Product Links    │   │    - Filter: client_id            │  │
│  │ 2. indexer.py:                │   │    - Similarity search (top-k)    │  │
│  │    - Recursive Splitter       │   │ 3. Link Extraction & Matching:    │  │
│  │      (1000 chars, 150 overlap)│   │    - Slug & Token matching        │  │
│  │    - Tag Client Metadata      │   │ 4. Prompt Assembly (Context + Q)  │  │
│  │    - Embed via Gemini/OpenAI  │   │ 5. LLM Generation (Gemini 2.5)    │  │
│  │    - Persist to ChromaDB      │   │ 6. Response Formatter             │  │
│  └───────────────┬───────────────┘   └───────────────────┬───────────────┘  │
└──────────────────┼───────────────────────────────────────┼──────────────────┘
                   │                                       │
                   ▼                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ISOLATED MULTI-TENANT STORAGE                          │
│                                                                             │
│   backend/data/vector_db/                                                   │
│   ├── shop_001/                                                             │
│   │   ├── chroma.sqlite3        <── Dedicated SQLite per Client             │
│   │   └── <uuid>/               <── Dedicated HNSW Index Segments (.bin)    │
│   ├── shop_002/                                                             │
│   │   ├── chroma.sqlite3                                                    │
│   │   └── <uuid>/                                                           │
│   └── rental_001/                                                           │
│       ├── chroma.sqlite3                                                    │
│       └── <uuid>/                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Deep-Dive: Multi-Client & Multi-Tenant Isolation

In any junior/internship interview, the interviewer will probe:  
**"How does multi-tenancy work? Where does client data live? How do you prevent Client A from querying Client B's data?"**

Here is the exact technical explanation of how this codebase achieves **Triple-Layer Multi-Tenant Isolation**:

### Layer 1: Physical File-System Directory Partitioning
The system does not dump all vectors into a monolithic database file. Instead, the persistent directory path is parameterized by `client_id`:
```python
# backend/services/indexer.py (Line 61)
client_db_path = os.path.join(Config.VECTOR_DB_PATH, client_id)
os.makedirs(client_db_path, exist_ok=True)
```
On disk, this generates distinct, isolated directory trees:
```
backend/data/vector_db/
  ├── shop_001/
  │     ├── chroma.sqlite3       (Metadata & document text for shop_001)
  │     └── 75212527-.../        (HNSW vector graph index binaries)
  └── shop_002/
        ├── chroma.sqlite3       (Completely independent SQLite DB)
        └── a819df31-.../        (Independent HNSW graph binaries)
```
If `shop_001` has 5,000 products and `shop_002` has 100 products, their SQLite tables and vector index graphs never touch each other.

### Layer 2: ChromaDB Collection Partitioning
Within ChromaDB, a named collection is bound strictly to `client_id`:
```python
# backend/services/indexer.py (Line 68 & 133)
vector_db = Chroma.from_texts(
    texts=all_chunks,
    metadatas=all_metadatas,
    embedding=embeddings,
    persist_directory=client_db_path,
    collection_name=client_id            # Collection matches Tenant ID
)
```

### Layer 3: Metadata Tagging & Retrieval Filtering
Every chunk generated during scraping is explicitly injected with metadata attributes:
```python
# backend/services/indexer.py (Line 120-124)
metadata = {
    "client_id": client_id,
    "source_url": source_url,
    "product_links": "|".join(product_urls) if product_urls else ""
}
all_metadatas.append(metadata)
```
When a chat request arrives, the retriever enforces a strict SQL/metadata constraint:
```python
# backend/services/chatbot.py (Line 327-330)
client_db_path = os.path.join(Config.VECTOR_DB_PATH, client_id)
db = Chroma(persist_directory=client_db_path, embedding_function=embeddings, collection_name=client_id)

# Retriever query is hard-filtered by client_id:
retriever = db.as_retriever(search_kwargs={'filter': {'client_id': client_id}})
```

### Why this is a "Defense-in-Depth" Architecture:
Even if a developer makes a coding error in the metadata filter, the query is already constrained to `shop_001`'s isolated SQLite database on disk. Even if the directory loading failed, the metadata filter rejects chunks with a mismatching `client_id`. Data cannot cross tenant boundaries.

---

## 4. Line-by-Line / Module-by-Module Codebase Walkthrough

### 4.1 Backend Entry & Core Configuration

#### [`backend/core/config.py`](file:///c:/Project/chatbot-rag/backend/core/config.py)
* **What it does:** Centralized configuration management using `python-dotenv`.
* **Key Components:**
  * `GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")`: Read from `.env`. Used for Google Generative AI embeddings and Gemini LLM.
  * `OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")`: Optional fallback provider.
  * `VECTOR_DB_PATH`: Dynamically resolves the persistent storage folder on disk (`backend/data/vector_db`) relative to the file path.
  * `Config.validate()`: Fails fast on startup if `GOOGLE_API_KEY` is absent.

#### [`backend/api/main.py`](file:///c:/Project/chatbot-rag/backend/api/main.py)
* **What it does:** The primary FastAPI application instance.
* **Key Components:**
  * **CORS Middleware (Lines 32–41):** Configures allowed browser origins via `ALLOWED_ORIGINS` env var (e.g., `http://localhost:3000`, `http://localhost:8080`). Allows `allow_credentials=True`, all HTTP methods (`*`), and all headers.
  * **Router Mounting (Lines 44–45):** Mounts `/ingest` router and `/chat` router.
  * **System Endpoints (Lines 48–82):** Exposes `GET /health` (readiness probe) and `GET /` (service directory listing).
  * **Custom OpenAPI Security (Lines 84–109):** Injects `X-API-Key` security scheme into the Swagger UI (`/docs`), allowing interactive testing with authentication headers.
  * **Global Exception Handlers (Lines 112–134):** Catches both `HTTPException` and unhandled standard `Exception` to return structured JSON responses instead of crashing the server.

---

### 4.2 Security & Authentication Layer

#### [`backend/api/middleware/auth.py`](file:///c:/Project/chatbot-rag/backend/api/middleware/auth.py)
* **What it does:** Validates incoming requests using API key headers.
* **Mechanism:**
  * Uses FastAPI's `APIKeyHeader(name="X-API-Key")`.
  * `APIKeyValidator.get_valid_api_key()`: Retrieves `API_KEY` from environment variables.
  * `APIKeyValidator.verify_api_key(api_key)`: Checks `if api_key != valid_key: raise HTTPException(401, "Invalid API key")`.
  * Injected as a dependency (`Depends(API_KEY_HEADER)`) in `/ingest` and `/chat` routes.

---

### 4.3 Ingestion & Web Scraping Pipeline

#### [`backend/services/scraper.py`](file:///c:/Project/chatbot-rag/backend/services/scraper.py)
This is the data collection engine. It transforms raw, messy e-commerce websites into clean, RAG-digestible text.

* **1. Single Page Scraping (`scrape_website`, Lines 11–28):**
  * Spoofs a real desktop browser header: `headers = {"User-Agent": "Mozilla/5.0"}`.
  * Requests HTML with a 10-second timeout.
  * Parses HTML using `BeautifulSoup(response.text, 'html.parser')`.
  * **Crucial Step:** Calls `extract_product_urls_from_html()` *before* modifying or deleting DOM elements.
  * **Noise Decomposition (Line 23–24):** Destroys junk tags that cause LLM confusion:
    ```python
    for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
        element.decompose()  # Physically deletes element from DOM tree
    ```
  * Extracts remaining visible text cleanly: `soup.get_text(separator=' ', strip=True)`.

* **2. Product URL Pattern Matching (`extract_product_urls_from_html`, Lines 31–79):**
  * Finds all `<a>` tags with `href`.
  * Resolves relative URLs to absolute URLs using `urllib.parse.urljoin(base_url, href)`.
  * Filters URLs against e-commerce patterns:
    * `/products/`, `/product/`, `/item/`, `/p/`, `/sku/`, `/buy/`.
  * Filters out marketing tracking clutter: excludes URLs containing `utm_`.

* **3. Sitemap Crawler (`fetch_sitemap_urls`, Lines 82–162):**
  * Auto-discovers the sitemap at `{scheme}://{netloc}/sitemap.xml`.
  * Parses XML with `xml.etree.ElementTree`.
  * **Handles Nested Sitemaps (`sitemapindex`):** If the sitemap contains child `<sitemap>` nodes (common in Shopify and WooCommerce), it recursively fetches each child sitemap and extracts all underlying `<url><loc>` elements.

* **4. URL Filtering & Rate Limiting (`filter_product_pages` & `scrape_multiple_urls`, Lines 164–264):**
  * Excludes invalid links: `mailto:`, `tel:`, `#`, sorting parameters (`?sort=`, `?filter=`), `logout`, `cart/delete`.
  * Limits batch crawling to `max_urls=50` to prevent infinite crawling or timeouts.
  * Adds polite rate-limiting: `time.sleep(rate_limit_delay)` (1 second between requests) to prevent target servers from IP-banning the scraper.

---

### 4.4 Chunking, Embedding & Vector Storage

#### [`backend/services/indexer.py`](file:///c:/Project/chatbot-rag/backend/services/indexer.py)
This file bridges the gap between raw text and vector representations.

* **1. Embedding Provider Selection (`get_embeddings`, Lines 12–36):**
  * **Google Generative AI (Default):** `GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")`. High semantic accuracy, fast vector generation.
  * **OpenRouter (Alternative):** `OpenAIEmbeddings(model="text-embedding-3-small", base_url="https://openrouter.ai/api/v1")`.

* **2. Idempotency & Deduplication Check (Lines 65–83):**
  * Checks if data already exists in ChromaDB for this client.
  * If `force_reindex=False` and vectors exist: skips re-scraping and returns `{"status": "already_indexed"}`. This saves massive API embedding costs and scraping time!
  * If `force_reindex=True`: deletes the directory with `shutil.rmtree(client_db_path)` and indexes fresh data.

* **3. Text Chunking Math (Lines 101–103):**
  ```python
  splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
  ```
  * **`chunk_size=1000`:** Approximately 200–250 words per chunk. Fits an entire product description, specifications, and pricing without fragmentation.
  * **`chunk_overlap=150`:** Approximately 30–35 words of overlap between consecutive chunks. Prevents semantic context from being sliced in half at sentence boundaries.

* **4. Metadata Association & ChromaDB Writing (Lines 109–137):**
  * Tags each chunk with:
    * `client_id`: The tenant identifier.
    * `source_url`: The exact webpage the text came from.
    * `product_links`: Pipe-delimited list of product URLs found on that page (`"url1|url2"`).
  * Writes into ChromaDB using HNSW indexing and persists on disk.

---

### 4.5 Retrieval & Chatbot Intelligence Engine

#### [`backend/services/chatbot.py`](file:///c:/Project/chatbot-rag/backend/services/chatbot.py)
The core RAG reasoning loop. It combines query intent classification, vector retrieval, contextual prompt templating, and post-generation link synthesis.

* **1. LLM Provider Flexibility (Lines 16–17 & 308–320):**
  * Provider toggle: `CHAT_API_PROVIDER = "openrouter"` or `"google"`.
  * Google Model: `ChatGoogleGenerativeAI(model="gemini-2.5-flash", convert_system_message_to_human=True)`.
  * OpenRouter Model: `ChatOpenAI(model="openrouter/auto")`.

* **2. Query Intent Classification:**
  * **Store Info Query (`_is_store_info_query`, Lines 208–217):** Matches keywords ("shop name", "store", "contact", "address", "phone", "email").
  * **Product Query (`_is_product_query`, Lines 219–227):** Matches keywords ("product", "power bank", "price", "cheapest", "recommend").
  * **Link Intent (`_wants_links`, Lines 197–205):** Matches keywords ("link", "url", "website", "buy", "purchase", "order", "where to buy").

* **3. Vector Search & Metadata Link Extraction (Lines 258–292):**
  * Performs similarity search: `db.similarity_search_with_score(user_query, k=10, filter={'client_id': client_id})`.
  * Unpacks metadata: Reads `doc.metadata["product_links"]`, splits by `|`, and deduplicates into a candidate list of URLs.

* **4. Product Link Matching (`_filter_product_links`, Lines 161–195):**
  * Extracts product names bolded in the LLM answer (`**Product Name**`).
  * Converts the name to a slug (e.g., `"Aspor A337 Power Bank"` → `"aspor-a337-power-bank"`).
  * Matches the slug against the URL candidates.
  * If no bold names match, extracts query tokens (`_extract_query_tokens`) and matches tokens against URLs. Returns top 5 relevant links.

* **5. Dynamic System Prompts (Lines 342–370):**
  * **Store Info Prompt:** Tells the LLM to strictly output the store name without reciting product catalogs.
  * **Product Query Prompt:** Strictly formats items into structured blocks:
    ```
    1. **Product Name**
    Description: ...
    Price: Rs X,XXX
    Link: https://...
    ```
  * **General Prompt:** Answers questions using context; omits links unless requested.

* **6. Modern LangChain Chain Execution (Lines 376–381):**
  ```python
  question_answer_chain = create_stuff_documents_chain(llm, prompt)
  rag_chain = create_retrieval_chain(retriever, question_answer_chain)
  response = rag_chain.invoke({"input": user_query, "product_links": links_block})
  ```
  Uses the standard LangChain LCEL (LangChain Expression Language) retrieval chain.

* **7. Post-Processing & Deduplication (Lines 388–409):**
  * If the user didn't ask for links, strips any rogue URLs generated by the LLM (`_remove_link_lines`).
  * Checks `_answer_contains_links(answer, filtered_links)`: If the LLM already embedded the links in the markdown answer, it returns an empty `product_links` list to prevent the frontend widget from rendering duplicate links!

---

### 4.6 Embeddable Frontend Widget & Client Proxy Pattern

#### [`widget/rag-chat-widget.umd.js`](file:///c:/Project/chatbot-rag/widget/rag-chat-widget.umd.js)
* **What it is:** A standalone Universal Module Definition (UMD) JavaScript file (~11KB) that can be embedded into any third-party website via a single `<script>` tag.
* **Key Features:**
  * Self-executing IIFE `(function(global) { ... })(window)`.
  * Automatically injects CSS styles (`<style>`) and chat DOM (`.rag-chat-widget`) upon `DOMContentLoaded`.
  * Renders a floating circular chat bubble (💬) that toggles the chat window.
  * Handles Enter key submissions, auto-scrolls to the bottom, and renders markdown bullets (`*`, `-`), bold text (`**text**`), and clickable hyperlinks.
  * Renders a dedicated **🔗 Product Links** section when the API response returns `product_links`.

#### The Client Proxy Pattern ([`backend/CLIENT_PROXY_GUIDE.md`](file:///c:/Project/chatbot-rag/backend/CLIENT_PROXY_GUIDE.md))
* **The Problem:** The backend `/chat` endpoint requires `X-API-Key: sk_live_...`. If the frontend widget made requests directly to `http://api.rag.com/chat`, the client's private API key would be visible to any user who opens DevTools → Network tab!
* **The Solution (Backend-For-Frontend Proxy):**
  ```
  Visitor Browser (Widget) ──[No Key]──> Client Server (Proxy:3000) ──[X-API-Key]──> RAG Backend (8000)
  ```
  1. The widget sends queries to the client's own backend (`http://localhost:3000/chat`).
  2. The client's server reads `RAG_API_KEY` from its local server `.env`.
  3. The client's server forwards the request to the RAG backend with the secret `X-API-Key` header.
  4. The API key remains 100% confidential.

---

### 4.7 Dockerization & DevOps Infrastructure

* **[`docker/docker-compose.yml`](file:///c:/Project/chatbot-rag/docker/docker-compose.yml):**
  * Orchestrates two microservices:
    1. `backend`: Built from `docker/backend.Dockerfile`. Runs FastAPI on port 8000. Mounts `../backend/data/vector_db:/app/backend/data/vector_db` so vector data survives container restarts.
    2. `widget`: Built from `docker/widget.Dockerfile`. Runs Alpine Nginx on port 8080 to serve static `.umd.js` widget files.
* **[`docker/nginx.conf`](file:///c:/Project/chatbot-rag/docker/nginx.conf):**
  * Configures Nginx with CORS headers (`Access-Control-Allow-Origin: *`) so any external client website can load the widget script without browser security errors.

---

## 5. Key Technical Decisions & Technology Stack Rationale

Interviewers often ask: *"Why did you pick this specific tech stack instead of industry alternatives?"* Here is the exact architectural justification for every major piece of the system:

### 5.1 Why Each Core Technology Was Chosen

#### 1. Why FastAPI (vs. Flask / Django / Express)?
* **Asynchronous Non-Blocking I/O (ASGI):** FastAPI is built on Starlette and Uvicorn. In AI/RAG applications, operations like scraping websites, calling Google Gemini APIs, and retrieving embeddings take hundreds of milliseconds to seconds. Traditional WSGI frameworks (like standard Flask or Django) block worker threads while waiting for external HTTP requests. FastAPI's native `async/await` allows a single worker process to handle hundreds of concurrent user chats without stalling.
* **Automatic Data Validation via Pydantic:** Request payloads ([`IngestRequest`](file:///c:/Project/chatbot-rag/backend/api/models/schemas.py), [`ChatRequest`](file:///c:/Project/chatbot-rag/backend/api/models/schemas.py)) are strictly typed and auto-validated before hitting route handlers. Missing fields or bad URL inputs automatically return descriptive HTTP 422 errors without writing manual boilerplate checks.
* **Auto-Generated Interactive Documentation:** FastAPI automatically generates interactive Swagger/OpenAPI documentation at `/docs` and ReDoc at `/redoc`. This allowed testing `/ingest` and `/chat` directly from the browser with `X-API-Key` headers without needing Postman.
* **Modern Dependency Injection (`Depends`):** FastAPI provides clean dependency injection for security middleware ([`APIKeyValidator`](file:///c:/Project/chatbot-rag/backend/api/middleware/auth.py)), making testing, mocking, and authentication cleaner than Flask decorators or Django middleware.
* **High Raw Performance:** Benchmarks consistently place FastAPI among the fastest Python web frameworks, performing close to Node.js and Go.

#### 2. Why ChromaDB & SQLite 3 (`chroma.sqlite3`)?
* **What is `chroma.sqlite3`?** ChromaDB is an open-source, embedded vector database. It uses a **dual-engine architecture**:
  1. **SQLite 3 (`chroma.sqlite3`):** Acts as the relational metadata storage engine. It stores document text chunks, chunk IDs, collection mappings, metadata tags (`client_id`, `source_url`, `product_links`), and transaction logs with ACID guarantees.
  2. **HNSW Binary Index (`.bin` files):** ChromaDB saves high-dimensional vector graphs in binary format (`data_level0.bin`, `header.bin`, `length.bin`) to perform Approximate Nearest Neighbor (ANN) search via the HNSW algorithm.
* **Why ChromaDB + SQLite 3 was chosen over Cloud Vector DBs (Pinecone, Weaviate, Milvus):**
  * **Zero Infrastructure Overhead (In-Process / Serverless):** ChromaDB runs directly inside the Python process and writes to the local file system. It does not require hosting an external database cluster, saving cloud costs.
  * **Natural Multi-Tenant File Isolation:** Because SQLite databases are completely self-contained single files on disk, isolating clients is as simple as creating `backend/data/vector_db/<client_id>/chroma.sqlite3`. Client databases can be copied, backed up, or deleted (`shutil.rmtree`) without affecting any other client.
  * **Rich Metadata Filtering:** ChromaDB allows filtering vector searches by metadata attributes (`filter={'client_id': client_id}`), enabling both vector similarity and hard tenant boundary enforcement in a single query.
  * **Zero Cost for Prototyping:** Ideal for internal pilot projects and client demonstrations where spinning up a $70/month Pinecone pod is cost-prohibitive.

#### 3. Why Google Gemini 2.5 Flash & Gemini Embeddings (vs. OpenAI)?
* **Ultra-Fast Latency (Time-To-First-Token):** Gemini 2.5 Flash is designed specifically for high-speed, cost-efficient conversational AI, making it ideal for e-commerce widgets where users abandon slow chats.
* **Generous Context Window:** Handles large retrieved document contexts without truncation.
* **High-Accuracy Standardized Embeddings:** `models/gemini-embedding-001` provides 768-dimensional semantic embeddings optimized for search and retrieval.
* **Dual-Provider Architecture:** Through [`backend/services/chatbot.py`](file:///c:/Project/chatbot-rag/backend/services/chatbot.py), the codebase also supports OpenRouter (`openrouter/auto` and `text-embedding-3-small`), allowing seamless fallback if Google's API undergoes rate-limiting.

#### 4. Why LangChain (LCEL) for RAG Orchestration?
* **Modern LCEL (LangChain Expression Language):** The codebase uses modern LCEL primitives:
  * `create_stuff_documents_chain`: Automatically formats and injects retrieved context chunks into the prompt template.
  * `create_retrieval_chain`: Glues the ChromaDB vector retriever to the document chain into a unified pipeline.
* **Unified Model Abstraction:** Lets you switch between `ChatGoogleGenerativeAI` and `ChatOpenAI` by changing one variable without rewriting prompt structures or token parsers.
* **Battle-Tested Text Splitters:** Uses `RecursiveCharacterTextSplitter`, which splits along paragraph boundaries (`\n\n`), then sentences (`\n`), then spaces (` `), preserving semantic meaning better than naive string slicing.

#### 5. Why Vanilla JavaScript UMD for the Chat Widget?
* **Universal Module Definition (UMD):** The widget ([`rag-chat-widget.umd.js`](file:///c:/Project/chatbot-rag/widget/rag-chat-widget.umd.js)) is written in pure vanilla JavaScript without framework dependencies (no React, Vue, or Angular runtime).
* **Universal Drop-in Compatibility:** Clients can embed the widget on Shopify, WooCommerce, WordPress, Webflow, or custom HTML sites with just two `<script>` tags.
* **Tiny Footprint & Zero Build Requirement:** The bundle is only ~11KB, loads instantaneously, and requires zero npm builds or compilation on the host website.

#### 6. Why Docker & Nginx?
* **Containerized Microservices:** Decouples the Python FastAPI backend from the static widget host.
* **Nginx Static Asset CDN:** Nginx serves the `.umd.js` widget files with open CORS headers (`Access-Control-Allow-Origin: *`), ensuring web browsers on any third-party domain can download the widget without security errors.
* **Persistent Vector Mounts:** Docker Compose mounts `backend/data/vector_db` so SQLite vector databases persist across container restarts.

---

### 5.2 Engineering Decisions & Trade-Offs Matrix

| Decision | Why It Was Chosen | Alternative Considered | Trade-off / Rationale |
| :--- | :--- | :--- | :--- |
| **FastAPI vs. Flask** | Native `async/await`, Pydantic validation, automatic Swagger `/docs`. | Flask / Django | Flask is synchronous by default; Django is too heavyweight for microservices. |
| **ChromaDB (SQLite 3) vs. Pinecone** | Local file persistence; zero cloud infrastructure cost; simple directory-based multi-tenancy. | Pinecone / Milvus / Qdrant | Pinecone requires paid cloud subscriptions. ChromaDB allowed zero-cost local prototyping. |
| **RAG vs. Fine-Tuning** | Instant catalog updates; zero GPU training cost; grounded factual citations; no hallucinations. | Model Fine-Tuning (LoRA) | Fine-tuning costs thousands of dollars and cannot be updated every time a product price changes. |
| **Google Gemini Flash vs. GPT-4o** | Lower token latency, high context window, cost efficiency. | OpenAI GPT-4o | Gemini Flash provides instant responses for customer support widgets at a fraction of GPT-4o's cost. |
| **Recursive Chunking (1000/150)** | Preserves semantic paragraph structure while splitting large HTML pages. | Fixed Token Splitter | Fixed token splits cut sentences midway. 1000 chars fits an e-commerce product spec sheet perfectly. Overlap prevents context loss at chunk borders. |
| **Client-Side Proxy** | Absolute secrecy for client API keys. | Direct browser API calls | Direct calls expose API keys in browser devtools to malicious website visitors. |
| **Vanilla JS Widget vs. React Component** | Zero dependencies, works on any CMS (WordPress, Shopify) with ~11KB bundle. | React / Vue Widget Component | A React widget requires bundling React & ReactDOM (~150KB+) into every host website. |

---

## 6. Current System Limitations & Production Roadmap

In technical interviews, showing that you know the **limitations** of your own project demonstrates high engineering maturity. If an interviewer asks: *"What would you improve before launching to 100,000 users?"*, mention these points:

1. **Synchronous Scraping Blocks FastAPI Event Loop:**
   * *Current:* `POST /ingest` runs `requests.get()` synchronously. Scraping 50 pages can take 60 seconds, during which worker threads are blocked.
   * *Production Fix:* Use `httpx` with `async/await` and offload ingestion to a distributed task queue (**Celery + Redis**). Return a `job_id` immediately with a polling/webhook endpoint (`GET /ingest/status/{job_id}`).
2. **Stateless Chat (No Conversation Memory):**
   * *Current:* Each chat request is isolated. The user cannot ask: *"Does it come in black?"* after asking about a Dell laptop.
   * *Production Fix:* Introduce a `session_id`. Store conversation history in **Redis** with a 30-minute TTL, passing the last 5 turns to the LLM.
3. **Local SQLite Vector Database:**
   * *Current:* ChromaDB runs embedded SQLite on local disk. Cannot scale horizontally across multiple Docker containers.
   * *Production Fix:* Migrate to **PostgreSQL + pgvector** or a managed vector cluster (Qdrant / Milvus) with Row-Level Security (RLS) for multi-tenancy.
4. **Shared Single API Key in Environment:**
   * *Current:* One global `API_KEY` in `.env` validates all clients.
   * *Production Fix:* Relational DB table `clients (id, name, api_key_hash, rate_limit)` using `hmac.compare_digest` for timing-safe auth and per-tenant rate-limiting via `slowapi`.
5. **Streaming Responses (SSE):**
   * *Current:* Widget waits until the LLM finishes generating the entire answer before displaying text.
   * *Production Fix:* Implement **Server-Sent Events (SSE)** in FastAPI and stream tokens to the widget for a real-time ChatGPT-like typing animation.

---

## 7. Comprehensive Technical Interview Q&A

---

### Category A: Multi-Tenancy & Data Isolation

#### Q1: How does multi-tenancy work in this project, and how do you guarantee Client A cannot see Client B's data?
**Answer:**  
Multi-tenancy is enforced using a **three-tier isolation model**:
1. **File-System Isolation:** During ingestion, `client_db_path = os.path.join(Config.VECTOR_DB_PATH, client_id)`. Each client receives an isolated folder on disk containing its own `chroma.sqlite3` database and HNSW vector index files.
2. **Collection-Level Isolation:** ChromaDB collections are named explicitly after the `client_id`.
3. **Retrieval-Level Isolation:** All chunks have a `"client_id"` metadata tag. When querying, the retriever applies `filter={'client_id': client_id}`.  
Because Client A's ChromaDB instance opens only `vector_db/client_A/` and executes a metadata filter on `client_A`, it is physically impossible for queries to retrieve vectors belonging to `client_B`.

#### Q2: What are the trade-offs of storing each client's vector database in a separate folder on disk?
**Answer:**  
* **Advantages:** Absolute physical isolation; zero risk of cross-tenant data corruption; deleting a client's data is an instantaneous `shutil.rmtree(client_path)` operation; and backups can be done per-client.
* **Disadvantages / Trade-offs:** Does not scale well to tens of thousands of tenants because opening thousands of SQLite file descriptors consumes significant OS memory and file handles. In a large-scale SaaS, a single distributed vector database (such as PostgreSQL with `pgvector` or Qdrant) with tenant ID partitioning and connection pooling would be used instead.

#### Q3: How do you handle data updates if a client's website changes its prices or catalog?
**Answer:**  
In `backend/services/indexer.py`, the `index_website_data` function has a `force_reindex: bool` parameter. 
* By default (`force_reindex=False`), it checks `len(existing_db.get()['ids']) > 0`. If data exists, it skips indexing to avoid redundant scraping and API embedding costs.
* When updating (`force_reindex=True`), it safely purges the existing directory using `shutil.rmtree(client_db_path)`, creates a fresh directory, re-scrapes the sitemap, and generates new embeddings with up-to-date prices and product links.

#### Q4: If two clients have the exact same product on their websites, does the system reuse embeddings?
**Answer:**  
No. Because each client maintains an isolated ChromaDB collection and storage path, embeddings are generated independently for each tenant. While sharing embeddings would save minimal token costs, keeping them isolated ensures complete tenant privacy, allows each client to have different descriptions or pricing for the same item, and prevents complex multi-tenant access control vulnerabilities.

---

### Category B: RAG, Embeddings & Vector Search

#### Q5: What is RAG, and why is it preferred over fine-tuning for website customer support?
**Answer:**  
**Retrieval-Augmented Generation (RAG)** is an architecture where an external retrieval mechanism searches a knowledge base for facts relevant to a user's question, and injects those facts into the LLM's context prompt before generation.  
We choose RAG over Fine-Tuning because:
1. **Dynamic Updates:** When product prices or stock change, we simply update the vector database; fine-tuning would require retraining the entire model.
2. **Hallucination Prevention:** The LLM is instructed to answer *strictly* using the retrieved context.
3. **Traceability:** RAG allows returning exact source URLs and product links alongside answers.
4. **Cost & Latency:** Vector retrieval takes ~10ms and costs fractions of a cent, whereas fine-tuning requires specialized GPUs and significant training time.

#### Q6: Why did you choose a chunk size of 1000 characters and an overlap of 150 characters?
**Answer:**  
* **Chunk Size (1000 chars / ~200 words):** In e-commerce websites, product descriptions, key technical specs, and warranty policies typically fit within 150–250 words. A smaller chunk (e.g., 200 chars) would break a product title away from its price and description. A larger chunk (e.g., 5000 chars) would dilute the vector embedding with irrelevant text from adjacent sections, reducing retrieval precision.
* **Chunk Overlap (150 chars / ~30 words):** Text splitters can slice paragraphs mid-sentence. Overlap ensures that the semantic boundary between two chunks contains repeated context, so a question matching text at the cut point doesn't lose meaning in either chunk.

#### Q7: How does vector similarity search work under the hood in ChromaDB?
**Answer:**  
1. When text chunks are indexed, an embedding model (like `gemini-embedding-001`) maps each chunk into a high-dimensional dense vector (e.g., 768 dimensions).
2. ChromaDB indexes these vectors using the **HNSW (Hierarchical Navigable Small World)** algorithm—a multi-layered graph data structure that performs fast Approximate Nearest Neighbor (ANN) search in logarithmic time $O(\log N)$.
3. When a user asks a question, the question is converted into an embedding vector using the exact same model.
4. ChromaDB computes cosine similarity (or L2 Euclidean distance) between the query vector and indexed vectors to return the top-$k$ nearest document chunks.

#### Q8: Why does ChromaDB use SQLite 3 (`chroma.sqlite3`), and how does its dual-storage engine work?
**Answer:**  
ChromaDB uses a **hybrid dual-storage architecture**:
1. **SQLite 3 (`chroma.sqlite3`) for Relational & Metadata Storage:** SQLite 3 is an embedded, ACID-compliant relational database engine. ChromaDB uses it to store:
   * Document chunk texts (`documents` table)
   * Metadata key-value pairs (`client_id`, `source_url`, `product_links`)
   * Collection schemas, embeddings mappings, and write-ahead logs (WAL)
2. **HNSW Binary Files (`.bin` files) for Vector Indexing:** SQLite 3 is not designed for high-dimensional vector math. Therefore, vector embeddings and the multi-layered graph index are stored in binary segment files (`data_level0.bin`, `header.bin`, `length.bin`) managed by the `hnswlib` C++ library.
* **Why this is powerful:** When a query arrives with a metadata filter (`filter={'client_id': 'shop_001'}`), SQLite 3 filters the candidate document IDs rapidly using standard B-tree indexing, and HNSW computes similarity only across those filtered candidates.

#### Q9: Why not just use a traditional relational database (like MySQL or vanilla PostgreSQL) or MongoDB for the entire RAG pipeline?
**Answer:**  
* **Lack of Vector Indexing:** Standard relational or document databases are designed for scalar comparisons (`=`, `<`, `LIKE`, B-tree indexing). They cannot perform Approximate Nearest Neighbor (ANN) search over high-dimensional vectors (e.g., 768-dimensional float arrays). To find similar text in MySQL, you would have to calculate cosine distance against every single row using a full table scan ($O(N)$ brute-force), which takes seconds or minutes at scale.
* **ChromaDB's Specialized Advantage:** ChromaDB includes built-in HNSW graph indexing that executes similarity searches in $O(\log N)$ time (typically < 15ms), combined with seamless metadata filtering and embedding function bindings.
* **Production Path:** In an enterprise production setting, rather than pure ChromaDB, we could use **PostgreSQL with the `pgvector` extension**, which adds HNSW and IVFFlat vector indexing directly into a scalable relational database with connection pooling and Row-Level Security.

#### Q10: What embedding models does your project support, and why is it critical to use the same model for indexing and querying?
**Answer:**  
The project supports Google's `models/gemini-embedding-001` (default) and OpenRouter's `text-embedding-3-small`.  
**Critical Principle:** The embedding model used during ingestion *must* be identical to the model used during chat retrieval. Different models map semantic concepts into completely different vector spaces with different dimensionalities and coordinate geometries. Comparing a Google embedding query against an OpenAI embedding database would produce meaningless mathematical noise.

#### Q11: What happens if the user's question is completely unrelated to the client's website?
**Answer:**  
In `backend/services/chatbot.py`, the system prompts explicitly mandate:
```
"Use the following pieces of retrieved context to answer the question. If you don't know the answer, say that you don't know."
```
If the vector database returns chunks with low similarity scores that do not contain the answer, the LLM adheres to the system prompt and responds that it does not have that information, preventing hallucination.

---

### Category C: Scraping, Ingestion & Data Processing

#### Q10: How does your scraper avoid extracting garbage HTML (navbars, footers, tracking scripts)?
**Answer:**  
In `backend/services/scraper.py`, BeautifulSoup parses the HTML tree. Before extracting text, it physically decomposes unwanted DOM elements:
```python
for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
    element.decompose()
```
`element.decompose()` removes the tag and all its children from the parse tree. Afterwards, `soup.get_text(separator=' ', strip=True)` extracts clean, human-readable body text without cookie banners, header links, or JavaScript code.

#### Q11: How does the scraper discover all pages on an e-commerce website?
**Answer:**  
It uses `fetch_sitemap_urls(base_url)`:
1. It requests `{base_url}/sitemap.xml`.
2. It parses the XML with `xml.etree.ElementTree`.
3. It detects whether the root is a standard `<urlset>` or a `<sitemapindex>`.
4. If it is a `sitemapindex` (parent sitemap linking to multiple child sitemaps), it iterates through each child sitemap URL, fetches them, and extracts the final `<loc>` page URLs.
5. If no sitemap exists, it falls back gracefully to scraping the single target URL.

#### Q12: How are product links extracted and matched to user answers?
**Answer:**  
1. **Extraction:** During scraping, `extract_product_urls_from_html()` inspects all `<a>` tags before DOM decomposition, identifies URLs matching product patterns (`/products/`, `/item/`, `/sku/`, `/buy/`), and converts relative paths to absolute URLs.
2. **Metadata Tagging:** These URLs are stored inside chunk metadata as pipe-separated strings (`"url1|url2"`).
3. **Retrieval & Filtering:** During chat, `_extract_product_links_from_db()` fetches candidate links from retrieved chunks. `_filter_product_links()` inspects product names bolded in the LLM's response (`**Product Name**`), slugifies the name (e.g. `aspor-a337-power-bank`), and matches it against candidate URL slugs.
4. **Deduplication:** If the LLM already inserted links into the markdown body, `_answer_contains_links()` suppresses the separate `product_links` list to prevent duplicate links in the widget.

#### Q13: What measures prevent your web scraper from getting blocked by anti-bot systems?
**Answer:**  
1. **User-Agent Spoofing:** Requests include `headers = {"User-Agent": "Mozilla/5.0"}` so target web servers treat the request as a standard desktop browser rather than a Python `requests` bot.
2. **Rate Limiting:** `time.sleep(rate_limit_delay)` pauses for 1 second between consecutive page requests.
3. **Page Caps:** It limits batch crawling to `max_urls=50` to avoid triggering DDoS firewalls or IP rate limits.

---

### Category D: API Architecture, Security & Proxying

#### Q14: Why did you choose FastAPI over Flask or Django for building this backend?
**Answer:**  
1. **Asynchronous I/O (ASGI):** AI applications are heavily I/O-bound. Waiting for Google Gemini responses or embeddings takes 500ms–2000ms. In synchronous WSGI frameworks like Flask or Django, each waiting request ties up a worker thread. FastAPI's native `async/await` uses an event loop, allowing thousands of concurrent chat sessions on minimal server resources.
2. **Pydantic Validation:** Models like `IngestRequest` and `ChatRequest` enforce strict runtime type validation and automatic serialization, catching malformed JSON requests before they touch business logic.
3. **Interactive OpenAPI (`/docs`):** Automatically generates interactive Swagger documentation, drastically speeding up frontend integration and widget testing.
4. **Clean Dependency Injection:** FastAPI's `Depends()` allows clean injection of API key authentication (`APIKeyValidator`) and database connections without relying on messy global variables or custom decorators.
5. **Speed & Lightweight Footprint:** FastAPI runs on Starlette and Uvicorn, offering near C-level speed while avoiding Django's heavyweight ORM and admin overhead, which were unnecessary for this microservice.

#### Q15: What is ASGI vs. WSGI, and why does it matter for an LLM application?
**Answer:**  
* **WSGI (Web Server Gateway Interface):** The traditional synchronous Python standard (used by Flask, Django). It handles requests sequentially per worker thread. If 10 users ask an LLM a question simultaneously and each generation takes 2 seconds, a 4-worker WSGI server will leave 6 users stalled in the connection queue.
* **ASGI (Asynchronous Server Gateway Interface):** The modern asynchronous standard (used by FastAPI, Starlette, Uvicorn). When a request pauses to await an external LLM API response or database I/O, the single thread yields control back to the event loop to process other incoming user queries or widget chats. For AI applications with high external API latency, ASGI provides exponentially higher throughput and lower memory consumption.

#### Q16: Why do you need a Backend Proxy between the widget and the FastAPI server?
**Answer:**  
The FastAPI `/chat` endpoint requires an `X-API-Key` authentication header to protect backend compute and LLM token budgets.  
If the client-side JavaScript widget called the FastAPI backend directly, the client's `X-API-Key` would have to be hardcoded in the frontend script, allowing any website visitor to open DevTools, steal the key, and drain the client's LLM budget.  
By using a **Backend-For-Frontend (BFF) Proxy** (in Node.js, Python, or PHP), the widget sends unauthenticated requests to the client's own backend server. The client's server attaches the secret `X-API-Key` from its local environment and forwards the call to our RAG backend, keeping the secret key safe.

#### Q17: How does CORS middleware work in this project, and why is it needed?
**Answer:**  
FastAPI implements `CORSMiddleware`. Browsers enforce the Same-Origin Policy, preventing web pages from making API calls to a different domain/port unless the server explicitly sends `Access-Control-Allow-Origin` headers.  
In `backend/api/main.py`, `ALLOWED_ORIGINS` reads allowed domains (e.g., `http://localhost:3000`, `http://localhost:8080`) from `.env` and permits HTTP methods and headers so external websites can communicate with the backend. Similarly, the Nginx container serving the widget script sets `Access-Control-Allow-Origin: *` so any website can import the script.

#### Q18: What is the risk of doing `if api_key != valid_key` in `auth.py`, and how would you fix it?
**Answer:**  
Using standard Python string equality (`!=` or `==`) is vulnerable to a **Timing Attack**. Python compares strings character-by-character and returns `False` the moment it encounters the first mismatching character. An attacker measuring HTTP response times down to microseconds can theoretically deduce the API key character-by-character.  
**Fix:** Use `secrets.compare_digest` or `hmac.compare_digest(api_key, valid_key)`, which executes in constant time regardless of where the mismatch occurs.

#### Q19: What is SSRF (Server-Side Request Forgery), and is the `/ingest` endpoint vulnerable to it?
**Answer:**  
**SSRF** occurs when an attacker supplies a URL to a server, and the server fetches it without validation.  
Because `/ingest` accepts arbitrary URLs, an attacker could supply `http://169.254.169.254/latest/meta-data/` (AWS instance metadata) or `http://localhost:8000/internal-admin` to read internal cloud infrastructure secrets.  
**Fix:** Implement strict URL validation:
1. Ensure the scheme is strictly `http` or `https`.
2. Resolve DNS and reject loopback (`127.0.0.1`), private RFC 1918 subnets (`10.0.0.0/8`, `192.168.0.0/16`, `172.16.0.0/12`), and cloud metadata IP addresses.

---

### Category E: System Design & Scaling to Production

#### Q20: What happens to the system if 100 users trigger `/ingest` simultaneously?
**Answer:**  
Currently, `/ingest` is synchronous. 100 concurrent requests would spawn 100 web scraping threads, all making blocking HTTP calls and competing for CPU while chunking and writing to disk. This would exhaust the Uvicorn worker pool, block the FastAPI event loop, and cause HTTP request timeouts (504 Gateway Timeout).  
**Architectural Solution:**
Decouple ingestion into an asynchronous job pipeline:
1. The client sends `POST /ingest`.
2. FastAPI validates the request, enqueues an ingestion task into **Redis / RabbitMQ**, and immediately returns `202 Accepted` with a `job_id`.
3. Background **Celery / Arq workers** asynchronously crawl, chunk, and embed pages.
4. The client polls `GET /ingest/status/{job_id}` or receives a webhook when indexing completes.

#### Q21: How would you add multi-turn conversation memory so users can ask follow-up questions?
**Answer:**  
Currently, each query is stateless. To add memory:
1. Add a `session_id` string to `ChatRequest`.
2. Store chat history (last 6–10 turns) in **Redis** with a key like `chat:{client_id}:{session_id}` and a 30-minute expiration.
3. In LangChain, use `create_history_aware_retriever`. When a user asks a follow-up ("How much does *it* cost?"), an LLM rewrites the query into a standalone question based on previous conversation history ("How much does the Dell XPS 15 laptop cost?") before querying ChromaDB.
4. Pass the history to the LLM generation chain so the bot remembers earlier dialogue.

#### Q22: How would you scale the vector database from 10 clients to 10,000 clients?
**Answer:**  
1. **Replace Local ChromaDB with a Distributed Vector Store:** Migrate to **Qdrant**, **Milvus**, or **PostgreSQL with pgvector**.
2. **Namespace / Tenant Partitioning:** Modern vector databases support native tenant namespaces or payload filtering with indexed tenant fields. In `pgvector`, we would create a `document_chunks` table with a `client_id` column indexed with HNSW, and enable PostgreSQL **Row-Level Security (RLS)**.
3. **Read Replicas & Caching:** Deploy vector database read replicas. Use Redis to cache frequent query responses (e.g., store hours or return policies) using an MD5 hash of `(client_id, normalized_query)`.

#### Q23: How would you implement streaming responses for the chat widget?
**Answer:**  
1. In FastAPI, update `/chat` to return a `StreamingResponse` using **Server-Sent Events (SSE)** (`text/event-stream`).
2. Configure the LangChain LLM with `streaming=True` and invoke `astream()` or use an `AsyncIteratorCallbackHandler`.
3. In the frontend JavaScript widget, replace `fetch().then(r => r.json())` with the browser's `ReadableStreamDefaultReader` or `EventSource` API, appending incoming tokens to the chat bubble in real-time.

---

### Category F: Real-World Gotchas & Debugging Scenarios

#### Q24: What happens if an e-commerce website is built with React/Next.js and renders products client-side with JavaScript?
**Answer:**  
Our current scraper uses `requests.get()`, which downloads raw initial HTML. If a website is a Single Page Application (SPA) where content is rendered dynamically via client-side JavaScript, `requests.get()` will return an empty `<div id="root"></div>` without product text.  
**Solution:** Integrate a headless browser automation tool like **Playwright** or **Selenium**, or use a scraping proxy service (like ScrapingBee / Firecrawl) that executes JavaScript before extracting the DOM.

#### Q25: Why do we convert system messages to human messages for Gemini in `chatbot.py` (`convert_system_message_to_human=True`)?
**Answer:**  
Earlier versions of Google's Gemini API did not support a dedicated `"system"` role in the same way OpenAI does, or had strict requirements on where system instructions could be placed. Setting `convert_system_message_to_human=True` ensures LangChain reformats system instructions into the human prompt payload, guaranteeing broad compatibility across different Google Generative AI model versions without runtime API errors.

#### Q26: How do you verify which Google Generative AI models your API key has access to?
**Answer:**  
The repository contains a dedicated diagnostic tool in [`tests_and_scripts/diagnose.py`](file:///c:/Project/chatbot-rag/tests_and_scripts/diagnose.py). It initializes `google.generativeai`, calls `genai.list_models()`, and prints all active embedding and chat models supported by the provisioned API key, helping diagnose model deprecation or quota issues.

---

## 8. Candidate Cheatsheet: 1-Minute Pitch & 5-Minute Technical Walkthrough

### 🎤 The 1-Minute Elevator Pitch
*(Use this when the interviewer says: "Tell me about this RAG Chatbot project on your resume.")*

> "I built a Multi-Tenant Retrieval-Augmented Generation (RAG) customer support platform. It allows e-commerce businesses to input their website URL, automatically crawl their catalog using XML sitemaps, clean the HTML, and generate vector embeddings stored in an isolated ChromaDB vector database.
> 
> When visitors chat with the embeddable JavaScript widget on the client's store, the system retrieves relevant chunks using cosine similarity, applies specialized intent prompts, and generates accurate, hallucination-free answers with clickable product links using Google Gemini Flash.
> 
> What makes the project unique is its multi-tenant architecture—data is strictly isolated per client across the file system, collection, and metadata layers—and its client-side proxy security pattern, which keeps client API keys confidential. The entire system is containerized with Docker and Nginx."

---

### 🎙️ The 5-Minute Technical Walkthrough
*(Use this when the interviewer asks you to whiteboard or walk through the architecture end-to-end.)*

#### Step 1: Ingestion & Vector Storage Pipeline
* "Everything starts with the `POST /ingest` endpoint in FastAPI. When a store provides its URL and `client_id`, our `scraper.py` module looks for `sitemap.xml`. It handles nested sitemap indexes and extracts up to 50 valid URLs while filtering out search parameters and noise.
* For each page, BeautifulSoup extracts product URLs matching patterns like `/products/` or `/sku/` before stripping noise tags like scripts, headers, and footers.
* The clean text is passed to `indexer.py`, which splits it using `RecursiveCharacterTextSplitter` with 1,000-character chunks and a 150-character overlap.
* Each chunk is embedded using Google's `gemini-embedding-001` model and stored in an isolated ChromaDB directory partitioned by `client_id`. We also enforce an idempotency check so already-indexed websites aren't re-embedded unnecessarily."

#### Step 2: Query Processing & Retrieval Pipeline
* "When a visitor asks a question, the request hits `POST /chat` with the user query and `client_id`.
* The system loads the client's dedicated ChromaDB instance and creates a retriever with a hard `client_id` metadata filter.
* We run intent classification on the query. If the user asks for store hours or phone numbers, we invoke a concise store-info prompt. If they ask about items or prices, we extract candidate product links from the retrieved chunk metadata, match them to product names bolded in the LLM answer using slugification and token matching, and assemble a structured prompt.
* LangChain's `create_retrieval_chain` invokes Google Gemini 2.5 Flash, generating the final response and returning clean product links."

#### Step 3: Frontend Integration & Security
* "On the frontend, we built a standalone UMD JavaScript widget. Clients embed it via a `<script>` tag.
* To prevent leaking our API keys in the visitor's browser, we implemented a Backend-For-Frontend proxy pattern: the widget talks to the client's local server, which appends the secret `X-API-Key` before forwarding the request to our FastAPI backend.
* Finally, everything is orchestrated via Docker Compose: an Nginx container serves the static widget with open CORS headers, while Uvicorn powers the backend with mounted volumes for persistent vector storage."
