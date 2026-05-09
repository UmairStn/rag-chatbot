# RAG Chatbot Widget - Client Integration Guide

This guide shows how to securely integrate the RAG chatbot widget into your website using a backend proxy.

---

## 🔒 Security Architecture

Your widget will call **your own backend** (not ours directly), which then calls the RAG API with a hidden API key.

```
Your Website (Widget)
    ↓ (insecure, no key)
Your Backend Server
    ↓ (secure, API key hidden)
RAG API Backend
```

---

## 📋 Prerequisites

You need:
- A backend server in your preferred language (Python, Node.js, PHP, etc.)
- Your unique `client_id` (e.g., `shop_001`)
- Your `RAG_API_KEY` (provided by us)
- RAG API endpoint: `https://your-rag-api.com` (we'll provide your domain)

---

## 🐍 Option 1: Python/Flask Proxy

**File: `proxy.py`**

```python
from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.post("/api/chat")
def chat_proxy():
    """Proxy endpoint that hides RAG API key"""
    try:
        message = request.json.get("query")
        
        # Call RAG backend with YOUR hidden API key
        response = requests.post(
            "https://your-rag-api.com/chat",
            headers={"X-API-Key": os.getenv("RAG_API_KEY")},  # Hidden in .env
            json={
                "query": message,
                "client_id": os.getenv("CLIENT_ID")  # Your unique ID
            }
        )
        
        return response.json()
    except Exception as e:
        return {"error": "Failed to process request"}, 500

if __name__ == "__main__":
    app.run(port=5000, debug=False)
```

**File: `.env`**
```
RAG_API_KEY=sk_your_key_here
CLIENT_ID=shop_001
```

**Install dependencies:**
```bash
pip install flask requests python-dotenv
python proxy.py
```

---

## 🟢 Option 2: Node.js/Express Proxy

**File: `proxy.js`**

```javascript
const express = require('express');
const axios = require('axios');
require('dotenv').config();

const app = express();
app.use(express.json());

app.post('/api/chat', async (req, res) => {
    try {
        const message = req.body.query;
        
        // Call RAG backend with YOUR hidden API key
        const response = await axios.post(
            'https://your-rag-api.com/chat',
            {
                query: message,
                client_id: process.env.CLIENT_ID
            },
            {
                headers: {
                    'X-API-Key': process.env.RAG_API_KEY  // Hidden in .env
                }
            }
        );
        
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to process request' });
    }
});

app.listen(5000, () => console.log('Proxy running on port 5000'));
```

**File: `.env`**
```
RAG_API_KEY=sk_your_key_here
CLIENT_ID=shop_001
```

**Install dependencies:**
```bash
npm install express axios dotenv
node proxy.js
```

---

## 🐘 Option 3: PHP Proxy

**File: `proxy.php`**

```php
<?php
require 'vendor/autoload.php';

$dotenv = Dotenv\Dotenv::createImmutable(__DIR__);
$dotenv->load();

header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

try {
    $data = json_decode(file_get_contents('php://input'), true);
    $message = $data['query'] ?? '';
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => 'https://your-rag-api.com/chat',
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'X-API-Key: ' . $_ENV['RAG_API_KEY']  // Hidden!
        ],
        CURLOPT_POSTFIELDS => json_encode([
            'query' => $message,
            'client_id' => $_ENV['CLIENT_ID']
        ])
    ]);
    
    $response = curl_exec($ch);
    curl_close($ch);
    
    echo $response;
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to process request']);
}
?>
```

**File: `.env`**
```
RAG_API_KEY=sk_your_key_here
CLIENT_ID=shop_001
```

**Install dependencies:**
```bash
composer require vlucas/phpdotenv
```

---

## 📱 Widget Integration

Add this to your HTML:

```html
<!-- Load the widget -->
<script src="https://cdn.example.com/rag-chat-widget.umd.js"></script>

<!-- Configure widget to use YOUR proxy (not RAG API directly) -->
<script>
window.RAGChatBot = {
    apiEndpoint: "http://your-domain.com/api/chat",  // Your proxy!
    clientId: "shop_001"
};
</script>
```

That's it! The widget will now:
1. Send messages to **your proxy**
2. Your proxy sends to RAG API with **hidden API key**
3. RAG API responds through proxy back to widget
4. API key never exposed to browser ✅

---

## ✅ Testing Your Proxy

**Test with cURL:**
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello"}'
```

**Expected response:**
```json
{
  "response": "Hello! How can I help you?",
  "status": "success"
}
```

---

## 🚨 Important Security Notes

- ✅ **DO** store `RAG_API_KEY` in `.env` (never commit to git)
- ✅ **DO** add `.env` to `.gitignore`
- ❌ **DO NOT** expose API key in client-side code
- ❌ **DO NOT** expose API key in browser logs
- ✅ **DO** use HTTPS in production
- ✅ **DO** add rate limiting to your proxy

---

## 📞 Support

If you have issues:
1. Check that `.env` file exists with correct keys
2. Verify proxy server is running on the correct port
3. Check that widget `apiEndpoint` points to your proxy URL
4. Contact us with error logs

