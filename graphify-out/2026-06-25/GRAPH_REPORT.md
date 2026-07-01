# Graph Report - .  (2026-06-25)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 130 nodes · 145 edges · 32 communities (22 shown, 10 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9310dffc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 28|Community 28]]

## God Nodes (most connected - your core abstractions)
1. `get_chatbot_response()` - 13 edges
2. `index_website_data()` - 8 edges
3. `scrape_website_sitemap()` - 8 edges
4. `scrape_website()` - 7 edges
5. `chat()` - 6 edges
6. `ingest_website()` - 6 edges
7. `scrape_multiple_urls()` - 6 edges
8. `_filter_product_links()` - 5 edges
9. `backend/api/routes/chat.py` - 5 edges
10. `backend/services/indexer.py` - 5 edges

## Surprising Connections (you probably didn't know these)
- `ingest_website()` --calls--> `IngestResponse`  [INFERRED]
  backend/api/routes/ingest.py → backend/api/models/schemas.py
- `chat()` --calls--> `ChatResponse`  [INFERRED]
  backend/api/routes/chat.py → backend/api/models/schemas.py
- `chat()` --calls--> `get_chatbot_response()`  [EXTRACTED]
  backend/api/routes/chat.py → backend/services/chatbot.py
- `ingest_website()` --calls--> `index_website_data()`  [EXTRACTED]
  backend/api/routes/ingest.py → backend/services/indexer.py
- `main()` --calls--> `get_chatbot_response()`  [EXTRACTED]
  backend/main.py → backend/services/chatbot.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **RAG Ingestion and Query Pipeline** — backend_services_scraper_py, backend_services_indexer_py, backend_services_chatbot_py, chromadb [EXTRACTED 1.00]
- **Multi-Tenant Isolation Pattern** — backend_api_routes_ingest_py, backend_api_routes_chat_py, backend_services_indexer_py, backend_services_chatbot_py [EXTRACTED 1.00]

## Communities (32 total, 10 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (18): BaseModel, ChatRequest, ChatResponse, Config, ErrorResponse, IngestRequest, IngestResponse, Request and Response models for FastAPI endpoints (+10 more)

### Community 1 - "Community 1"
Cohesion: 0.18
Nodes (17): _answer_contains_links(), _extract_product_links_from_db(), _extract_product_names_from_answer(), extract_product_urls(), _extract_query_tokens(), _extract_shop_name(), _filter_product_links(), get_chatbot_response() (+9 more)

### Community 2 - "Community 2"
Cohesion: 0.19
Nodes (16): get_embeddings(), index_website_data(), Get embeddings model based on API provider          Args:         api_provide, Index website content and store vectors in ChromaDB          Args:         ur, extract_product_urls_from_html(), fetch_sitemap_urls(), filter_product_pages(), Scrape a single website URL and return clean text (+8 more)

### Community 3 - "Community 3"
Cohesion: 0.20
Nodes (12): backend/api/main.py, backend/api/middleware/auth.py, backend/api/models/schemas.py, backend/api/routes/chat.py, backend/api/routes/ingest.py, backend/services/chatbot.py, backend/services/indexer.py, backend/services/scraper.py (+4 more)

### Community 4 - "Community 4"
Cohesion: 0.17
Nodes (11): custom_openapi(), general_exception_handler(), health_check(), http_exception_handler(), Main FastAPI application FastAPI web service for RAG chatbot with website inges, Custom HTTP exception handler, Catch-all exception handler, Check API health status (+3 more)

### Community 5 - "Community 5"
Cohesion: 0.29
Nodes (5): APIKeyValidator, Authentication middleware for API key validation, Validates API keys for protecting endpoints, Get the valid API key from environment, Verify the provided API key matches the configured key                  Args:

## Knowledge Gaps
- **13 isolated node(s):** `$schema`, `plugin`, `@opencode-ai/plugin`, `Config`, `Widget + Backend Integration Guide` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `index_website_data()` connect `Community 2` to `Community 0`, `Community 6`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Why does `ingest_website()` connect `Community 0` to `Community 2`, `Community 5`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `get_chatbot_response()` connect `Community 1` to `Community 0`, `Community 6`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **What connects `$schema`, `plugin`, `@opencode-ai/plugin` to the rest of the system?**
  _43 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.12380952380952381 - nodes in this community are weakly interconnected._