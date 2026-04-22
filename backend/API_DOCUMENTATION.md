# RAG Chatbot Web Service - API Documentation

## Overview

This is a FastAPI-based web service that converts your RAG chatbot into a scalable HTTP API. It allows you to:
- **Ingest websites** via API endpoints
- **Chat with AI** using indexed website content
- **Multi-tenant support** with client-specific data isolation
- **API key authentication** for secure access

---

## Project Structure

```
backend/
├── api/                          # FastAPI application
│   ├── main.py                   # FastAPI app setup & routes
│   ├── routes/
│   │   ├── ingest.py            # POST /ingest endpoint
│   │   └── chat.py              # POST /chat endpoint
│   ├── middleware/
│   │   └── auth.py              # API key authentication
│   └── models/
│       └── schemas.py            # Pydantic request/response models
├── services/
│   ├── indexer.py               # Website indexing logic
│   ├── chatbot.py               # Chat response logic
│   └── scraper.py               # Web scraping
├── core/
│   ├── config.py                # Configuration
│   └── security.py              # Security utilities
├── data/
│   └── vector_db/               # Persisted vector database (survives restarts)
├── logs/
│   └── LOG_2026-04-18.md        # Activity logs
├── main.py                       # CLI mode (original)
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (create from .env.example)
└── .env.example                 # Environment template
```

---

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example .env file and update with your credentials:

```bash
cp .env.example .env
```

Update `.env` with:
```ini
GOOGLE_API_KEY=your_actual_google_api_key
API_KEY=your_secure_api_key_for_endpoints
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True
```

### 3. Run the Server

```bash
python -m api.main
```

The server will start at `http://localhost:8000`

---

## API Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "RAG Chatbot API",
  "version": "1.0.0"
}
```

---

### 2. Ingest Website

**Endpoint:** `POST /ingest`

**Headers:**
```
X-API-Key: your_api_key
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://www.example.com",
  "client_id": "shop_001"
}
```

**Response (Success - New):**
```json
{
  "status": "success",
  "message": "Successfully indexed website for shop_001",
  "chunks_indexed": 45,
  "client_id": "shop_001"
}
```

**Response (Already Indexed):**
```json
{
  "status": "already_indexed",
  "message": "Data already indexed for shop_001. Skipping...",
  "client_id": "shop_001"
}
```

**Error Response (400 - Bad Request):**
```json
{
  "status": "error",
  "error": "HTTP Exception",
  "message": "url and client_id are required"
}
```

**Error Response (401 - Unauthorized):**
```json
{
  "status": "error",
  "error": "HTTP Exception",
  "message": "Invalid API key"
}
```

---

### 3. Chat with Bot

**Endpoint:** `POST /chat`

**Headers:**
```
X-API-Key: your_api_key
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "What products do you offer?",
  "client_id": "shop_001"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "answer": "Based on the website content, we offer a wide range of electronics...",
  "client_id": "shop_001"
}
```

**Error Response (400 - Bad Request):**
```json
{
  "status": "error",
  "error": "HTTP Exception",
  "message": "query and client_id are required"
}
```

---

## Data Persistence

### Vector Database

- **Location:** `backend/data/vector_db/`
- **Type:** Chroma SQLite database
- **Multi-tenant:** Each client's data is isolated via `client_id`
- **Survives Restarts:** Data is persisted to disk and reloaded on server restart

### Data Structure

```
data/
└── vector_db/
    ├── chroma.sqlite3         # Main database file
    └── [UUID folders]/        # Collection data
```

The vector database stores:
- Website content chunks (1000 characters each with 150 char overlap)
- Embeddings (Google Gemini embeddings)
- Metadata (client_id for data isolation)

---

## Authentication

### API Key Protection

All endpoints (except `/health` and `/`) require an API key header:

```
X-API-Key: your_api_key_from_env
```

**Where to get it:**
- Set `API_KEY` in your `.env` file
- Pass it in the `X-API-Key` header with each request

**Example with cURL:**
```bash
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","client_id":"shop_001"}'
```

**Example with Python:**
```python
import requests

headers = {
    "X-API-Key": "your_api_key",
    "Content-Type": "application/json"
}

response = requests.post(
    "http://localhost:8000/ingest",
    headers=headers,
    json={"url": "https://example.com", "client_id": "shop_001"}
)
```

---

## Usage Examples

### Python Client

```python
import requests
import json

BASE_URL = "http://localhost:8000"
API_KEY = "your_api_key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# 1. Ingest a website
ingest_response = requests.post(
    f"{BASE_URL}/ingest",
    headers=headers,
    json={
        "url": "https://www.example.com",
        "client_id": "shop_001"
    }
)
print(ingest_response.json())

# 2. Chat with the bot
chat_response = requests.post(
    f"{BASE_URL}/chat",
    headers=headers,
    json={
        "query": "What are your products?",
        "client_id": "shop_001"
    }
)
print(chat_response.json())
```

### JavaScript/Fetch

```javascript
const BASE_URL = "http://localhost:8000";
const API_KEY = "your_api_key";

const headers = {
  "X-API-Key": API_KEY,
  "Content-Type": "application/json"
};

// 1. Ingest a website
fetch(`${BASE_URL}/ingest`, {
  method: "POST",
  headers: headers,
  body: JSON.stringify({
    url: "https://www.example.com",
    client_id: "shop_001"
  })
})
.then(res => res.json())
.then(data => console.log(data));

// 2. Chat with the bot
fetch(`${BASE_URL}/chat`, {
  method: "POST",
  headers: headers,
  body: JSON.stringify({
    query: "What are your products?",
    client_id: "shop_001"
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

---

## Documentation

- **Interactive API Docs (Swagger UI):** http://localhost:8000/docs
- **Alternative API Docs (ReDoc):** http://localhost:8000/redoc

---

## Deployment

### Local Development

```bash
python -m api.main
```

### Production (with Gunicorn)

```bash
gunicorn -w 4 -b 0.0.0.0:8000 api.main:app
```

### Environment Variables for Production

```ini
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=False
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
API_KEY=your_strong_secure_key_change_this
GOOGLE_API_KEY=your_google_key
```

---

## Troubleshooting

### API Key Error

**Error:** `Invalid API key`

**Fix:** Ensure `X-API-Key` header is set correctly and matches `API_KEY` in `.env`

### Vector DB Not Found

**Error:** `Vector database not initialized`

**Fix:** 
1. Run `/ingest` endpoint first to create the database
2. Check `VECTOR_DB_PATH` in `.env` is correct
3. Ensure `backend/data/vector_db/` folder exists

### Google API Key Error

**Error:** `GOOGLE_API_KEY missing or invalid`

**Fix:**
1. Get a valid Google API key from Google Cloud Console
2. Enable Generative Language API
3. Set `GOOGLE_API_KEY` in `.env`

### Port Already in Use

**Error:** `Address already in use`

**Fix:**
1. Change `API_PORT` in `.env`
2. Or kill the process using port 8000: `lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9`

---

## Multi-Tenant Architecture

### How Client Isolation Works

Each `client_id` has its own isolated:
- **Vector database collection** - Data is filtered by `client_id`
- **Embeddings** - Separate embeddings per client
- **Chat history** - Queries only search that client's data

### Example

```json
// Client A ingest
{
  "url": "https://shop-a.com",
  "client_id": "shop_a"
}

// Client B ingest (different website, different data)
{
  "url": "https://shop-b.com",
  "client_id": "shop_b"
}

// Client A chat (only searches Client A's data)
{
  "query": "What products do you have?",
  "client_id": "shop_a"
}
```

---

## Performance Optimization

### Reduce API Calls

- Duplicate indexing is prevented - already indexed clients skip re-embedding
- Vectors are cached locally in ChromaDB
- Chat queries use local similarity search, not external APIs

### Cost Optimization

- First ingest per client: 1 API call to Google (embedding generation)
- Subsequent ingests for same client: 0 API calls (skipped)
- Chat queries: 1 API call to Google (LLM response generation)

---

## License

This project is part of the chatbot-rag system.

---

## Support

For issues or questions:
1. Check logs in `backend/logs/`
2. Review API documentation at `/docs`
3. Check `.env` configuration
4. Verify Google API key is valid
