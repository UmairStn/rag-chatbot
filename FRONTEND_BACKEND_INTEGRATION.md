# Complete Frontend + Backend Integration Guide

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
│  │  │   React Component               ││                  │
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

### 1. Admin Dashboard → Backend (Training)

**Admin User Journey:**

```
Step 1: Admin Dashboard Opens
├─ URL: http://localhost:3000 (development)
├─ Loads: React admin interface

Step 2: Admin Configures
├─ Sets API Key: sk_live_xxxxx
├─ Sets Client ID: shop_001
├─ Enters Website URL: https://example.com

Step 3: Admin Clicks "Train Bot"
├─ Frontend validates inputs
├─ Sends POST request to /ingest
├─ Backend processes website
├─ ChromaDB stores embeddings
├─ Frontend shows success message

Step 4: Widget Code Generated
├─ Frontend displays installation code
├─ Admin copies code
├─ Admin adds code to their website
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
Step 1: Website Visitor Views Page
├─ Script tag loads chat widget
├─ Widget creates Shadow DOM
├─ React component mounts
├─ Chat bubble appears (bottom-right)

Step 2: Visitor Clicks Chat Bubble
├─ Chat window slides open
├─ Welcome message displays
├─ Input field ready

Step 3: Visitor Types Question
├─ "What products do you offer?"

Step 4: Widget Sends to Backend
├─ POST request to /chat endpoint
├─ Includes query and client_id
├─ Includes X-API-Key header

Step 5: Backend Processes
├─ Converts query to embedding
├─ Searches ChromaDB for relevant chunks
├─ Passes to LLM with context
├─ Returns AI response

Step 6: Response Displays in Widget
├─ Bot message appears
├─ Auto-scrolls to latest
├─ User can ask follow-up
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

### Frontend .env
```env
# Development
VITE_API_URL=http://localhost:8000
VITE_API_KEY=sk_test_xxxxx

# Production
VITE_API_URL=https://api.your-domain.com
VITE_API_KEY=sk_live_xxxxx
```

### Backend .env
```env
# API Configuration
API_KEY=sk_live_xxxxx
ALLOWED_ORIGINS=http://localhost:3000,https://your-domain.com

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

### Terminal 2: Start Frontend
```bash
cd c:\Project\chatbot-rag\frontend
npm install
npm run dev
# Running on http://localhost:3000
```

### Test Integration
1. Open http://localhost:3000 in browser
2. Enter API key in admin dashboard
3. Paste test URL (e.g., https://roamly-ten-tan.vercel.app/)
4. Click "Train Bot"
5. Copy generated widget code
6. Open your own test website
7. Paste widget code
8. Chat bubble should appear
9. Test sending a message

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

## Error Handling

### Frontend Error Messages
```typescript
// Invalid API key
"Invalid API Key"

// Missing fields
"Please fill in all fields"

// Network error
"Failed to ingest website"

// Chat error
"Sorry, I encountered an error. Please try again."
```

### Backend Error Messages
```json
{
  "detail": "Invalid API key"  // 401
}

{
  "detail": "url and client_id are required"  // 400
}

{
  "detail": "Failed to index website"  // 500
}
```

---

## Security Considerations

### API Key Protection
- ✅ Stored in localStorage (frontend)
- ✅ Sent in X-API-Key header
- ✅ Validated on backend
- ✅ Never exposed in logs

### CORS Configuration
```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",           # Development
    "https://your-domain.com",         # Production
]
```

### Client Isolation
```python
# All queries filtered by client_id
search_kwargs = {'filter': {'client_id': client_id}}
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

### Styling Conflicts
1. Widget uses Shadow DOM (isolated)
2. Check if browser supports Shadow DOM
3. Review browser compatibility (Chrome 77+)

### API Connection Issues
1. Verify VITE_API_URL is correct
2. Check backend CORS settings
3. Test with curl:
```bash
curl -X POST http://localhost:8000/health
```

---

## Performance Optimization

### Frontend
- Vite dev server: ~100ms HMR
- Production build: ~50KB minified
- Widget bundle: ~50KB
- Message rendering: React optimized

### Backend
- Embeddings cached in ChromaDB
- Multi-threaded request handling
- Response time: ~200-500ms
- Scales with database size

---

## Deployment Checklist

### Frontend Deployment
- [ ] Set VITE_API_URL to production backend
- [ ] Update VITE_API_KEY to production key
- [ ] Run `npm run build`
- [ ] Deploy dist/ to CDN/hosting
- [ ] Test all features

### Widget Deployment
- [ ] Run `npm run build:widget`
- [ ] Upload rag-chat-widget.umd.js to CDN
- [ ] Update widget URL in installation docs
- [ ] Test on multiple websites

### Backend Deployment
- [ ] Update ALLOWED_ORIGINS for frontend domain
- [ ] Set production GOOGLE_API_KEY
- [ ] Configure VECTOR_DB_PATH
- [ ] Test health endpoint
- [ ] Monitor logs

---

## Testing

### Admin Dashboard Test
```
✓ Enter URL and click Train
✓ See chunks_indexed > 0
✓ Copy widget code
✓ Code should contain apiUrl, apiKey, clientId
```

### Chat Widget Test
```
✓ Widget loads on test page
✓ Chat bubble visible
✓ Click bubble opens chat
✓ Type message and send
✓ Receive bot response
✓ Multiple messages work
✓ Mobile layout works
✓ CSS doesn't conflict
```

---

## Support & Documentation

- **Frontend README**: frontend/README.md
- **Frontend Setup**: frontend/SETUP.md
- **Widget Integration**: frontend/WIDGET_INTEGRATION.md
- **Backend API Docs**: backend/API_DOCUMENTATION.md

---

## Summary

The system is fully integrated and ready for:
1. ✅ Admin dashboard for training (frontend)
2. ✅ Embeddable chat widget (frontend)
3. ✅ Backend API endpoints (backend)
4. ✅ Vector database storage (ChromaDB)
5. ✅ Multi-tenant support
6. ✅ Production deployment

**All components communicate seamlessly!** 🚀
