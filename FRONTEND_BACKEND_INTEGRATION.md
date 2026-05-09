# Widget + Backend Integration Guide

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Customer's Website                       │
│                                                             │
│  <script src="rag-chat-widget.umd.js"></script>           │
│  ↓                                                          │
│  ┌─────────────────────────────────────┐                  │
│  │  Shadow DOM (CSS Isolated)          │                  │
│  │  ┌─────────────────────────────────┐│                  │
│  │  │   RAG Chatbot Widget            ││                  │
│  │  │   - Chat Bubble Button          ││                  │
│  │  │   - Chat Window                 ││                  │
│  │  │   - Message Display             ││                  │
│  │  │   - Input Form                  ││                  │
│  │  └─────────────────────────────────┘│                  │
│  └─────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                           ↓ HTTP API Calls
┌─────────────────────────────────────────────────────────────┐
│           Backend API (FastAPI)                             │
├─────────────────────────────────────────────────────────────┤
│  POST /ingest                                               │
│    ↓ Extract URL content                                   │
│    ↓ Split into chunks                                    │
│    ↓ Create embeddings                                    │
│    ↓ Store in ChromaDB                                    │
│                                                             │
│  POST /chat                                                 │
│    ↓ Retrieve relevant chunks (RAG)                       │
│    ↓ Pass to LLM with context                             │
│    ↓ Return AI-generated answer                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              Vector Database (ChromaDB)                      │
│              + LLM (Google Gemini)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration Flow

### 1. Training (API Docs)

**Workflow:**
```
Step 1: Open http://localhost:8000/docs
Step 2: Call POST /ingest with url + client_id
Step 3: Backend scrapes and indexes content
Step 4: Website is ready for chat
```

**HTTP Request:**
```http
POST http://localhost:8000/ingest
Content-Type: application/json
X-API-Key: sk_live_xxxxx

{
  "url": "https://example.com",
  "client_id": "shop_001"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Website indexed successfully",
  "chunks_indexed": 42,
  "client_id": "shop_001"
}
```

---

### 2. Chat Widget → Backend (Chat)

**End User Journey:**
```
Step 1: Website loads widget script
Step 2: Widget creates Shadow DOM
Step 3: Visitor opens chat
Step 4: Widget calls POST /chat with query + client_id
Step 5: Backend returns AI response
```

**HTTP Request:**
```http
POST http://api.example.com/chat
Content-Type: application/json
X-API-Key: sk_live_xxxxx

{
  "query": "What products do you offer?",
  "client_id": "shop_001"
}
```

**Response:**
```json
{
  "status": "success",
  "answer": "We offer a wide range of products including...",
  "client_id": "shop_001"
}
```

---

## Configuration

### Widget Snippet
```html
<script>
  window.RAGChatBot = {
    apiUrl: "https://api.your-domain.com",
    apiKey: "sk_live_xxxxx",
    clientId: "shop_001"
  };
</script>
<script src="https://cdn.your-domain.com/rag-chat-widget.umd.js"></script>
```

### Backend .env
```env
# API Configuration
API_KEY=sk_live_xxxxx
ALLOWED_ORIGINS=http://localhost:8080,https://your-domain.com

# Google API
GOOGLE_API_KEY=AIzaSy...

# Vector DB
VECTOR_DB_PATH=backend/data/vector_db
```

---

## Development Workflow

### Terminal 1: Start Backend
```bash
cd c:\Project\chatbot-rag\backend
conda activate rag-chatbot
python main.py
# Running on http://localhost:8000
```

### Terminal 2: Serve Widget (Docker)
```bash
cd c:\Project\chatbot-rag
docker compose up --build widget
# Widget available at http://localhost:8080
```

### Test Integration
1. Open http://localhost:8000/docs and call POST /ingest
2. Add the widget snippet to any test HTML page
3. Point the script URL to http://localhost:8080/rag-chat-widget.umd.js
4. Chat bubble should appear
5. Send a message and confirm a response

---

## API Endpoint Reference

### Health Check
```http
GET /health
Response: { status: "ok" }
```

### Website Ingestion
```http
POST /ingest
Content-Type: application/json
X-API-Key: required

Body:
{
  "url": "https://example.com",
  "client_id": "shop_001"
}

Response:
{
  "status": "success|already_indexed",
  "message": "string",
  "chunks_indexed": number,
  "client_id": "string"
}
```

### Chat Query
```http
POST /chat
Content-Type: application/json
X-API-Key: required

Body:
{
  "query": "User question",
  "client_id": "shop_001"
}

Response:
{
  "status": "success",
  "answer": "AI response",
  "client_id": "shop_001"
}
```

---

## Troubleshooting

### Widget Not Appearing
1. Check browser console for errors
2. Verify script URL is correct
3. Ensure window.RAGChatBot is configured
4. Check CORS headers in backend

### No Chat Responses
1. Verify website has been indexed
2. Check client_id matches
3. Verify API key is valid
4. Check backend is running

### API Connection Issues
1. Check backend CORS settings
2. Test with curl:
```bash
curl -X POST http://localhost:8000/health
```

---

## Summary

The system is ready for:
1. ✅ API-driven training via `/ingest`
2. ✅ Embeddable chat widget (UMD)
3. ✅ Backend API endpoints
4. ✅ Vector database storage (ChromaDB)
5. ✅ Multi-tenant support

**All components communicate seamlessly!** 🚀
