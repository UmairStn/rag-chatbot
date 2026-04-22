# 🤖 RAG Chatbot - Website AI Assistant

An AI-powered chatbot system that lets businesses train chatbots on their website content and embed them on any website with just a single line of code.

---

## 📝 Project Description

This is a **complete chatbot solution** for websites. Instead of building your own AI from scratch, you can:

1. **Train** - Paste your website URL once
2. **Generate** - Get a single line of code
3. **Embed** - Copy-paste on any website
4. **Chat** - Visitors ask questions, AI answers

That's it. Your website now has an AI assistant powered by your own content.

---

## 💡 The Problem We Solve

- ❌ Customers don't know your products/services
- ❌ Support teams are overwhelmed with repetitive questions
- ❌ Manual FAQs are outdated and ignored
- ❌ Building custom AI is expensive and complex

## ✅ Our Solution

- ✅ AI reads your website automatically
- ✅ Chat widget answers customer questions 24/7
- ✅ Uses YOUR content (not generic AI)
- ✅ Works on any website in seconds

---

## 🛠️ Technology Stack

### Backend (Server - What Powers Everything)
- **Python 3.12** - Programming language
- **FastAPI** - Web framework (super fast API)
- **Google Gemini AI** - LLM for intelligent responses
- **ChromaDB** - Database for storing website content
- **BeautifulSoup** - Website scraping
- **LangChain** - AI framework

### Widget (What Gets Embedded)
- **Single JavaScript file** - One UMD bundle
- **Shadow DOM** - Isolated styling (no CSS conflicts)
- **Works anywhere** - WordPress, Shopify, custom sites, static HTML
- **No dependencies** - Pure JavaScript, works in any browser

---

## 🚀 How Easy Is It to Add Widget to Your Website?

### Step 1: Copy the Widget Code
```javascript
<script>
  window.RAGChatBot = {
    apiUrl: "https://api.example.com",
    apiKey: "sk_live_xxxxx",
    clientId: "shop_001"
  };
</script>
<script src="https://cdn.example.com/rag-chat-widget.umd.js"></script>
```

### Step 2: Paste on Your Website
```html
<!-- Your website HTML -->
<html>
  <head>
    <title>My Website</title>
  </head>
  <body>
    <!-- Your content here -->
    
    <!-- Paste widget code at the bottom -->
    <script>
      window.RAGChatBot = {
        apiUrl: "https://api.example.com",
        apiKey: "sk_live_xxxxx",
        clientId: "shop_001"
      };
    </script>
    <script src="https://cdn.example.com/rag-chat-widget.umd.js"></script>
  </body>
</html>
```

### Step 3: Done!
Chat bubble appears in bottom-right corner automatically ✅

---

## 📊 What Happens When Users Chat

```
User: "Do you have free shipping?"
  ↓
Widget sends question to our server
  ↓
Server searches your website content
  ↓
Server uses AI to answer based on your content
  ↓
Answer appears in chat bubble
  ↓
User: "Great! How do I track my order?"
```

**The AI only knows what's on your website** - perfect, relevant answers every time.

---

## 🎯 Two Parts of This System

### 1️⃣ Backend API
**What it does:** Stores your website content, searches it, generates AI responses
**Technology:** Python FastAPI + Google Gemini + ChromaDB
**Where:** Cloud server (hidden from users)

### 2️⃣ Chat Widget
**What it does:** Appears on your website, lets customers chat
**Technology:** Single JavaScript file (no dependencies)
**Where:** Embedded on your website (visible to users)

---

## ⚙️ How It Actually Works (Technical)

```
TRAINING (One-time):
Website URL → Scraper reads all pages → Content split into chunks
  ↓
Chunks converted to vectors (AI-readable format)
  ↓
Vectors stored in database
  ↓
Done - bot is trained

CHAT (Every message):
User types question → Converted to vector
  ↓
Database finds similar content chunks
  ↓
AI reads those chunks + question
  ↓
AI generates answer
  ↓
Answer sent to widget
```

---

## ✨ Why This Is Easy

- ✅ **No coding** - Just copy-paste 2 lines
- ✅ **No setup** - Backend hosted for you
- ✅ **No dependencies** - Single JavaScript file
- ✅ **No CSS conflicts** - Shadow DOM isolation
- ✅ **Instant deployment** - Works immediately

---

## 💼 Real World Examples

### Example 1: E-commerce Store
```
Customer: "What's your return policy?"
AI: "Returns within 30 days for full refund..."
(pulled from your website)
```

### Example 2: SaaS Company  
```
User: "How do I reset my password?"
AI: "Go to Settings → Account → Reset Password..."
(from your help docs)
```

### Example 3: Service Business
```
Client: "What areas do you serve?"
AI: "We serve NYC, Boston, and Philadelphia..."
(from your service page)
```

---

## 🔐 Security & Privacy

- ✅ Each business gets their own API key
- ✅ Data isolated by business ID
- ✅ No data sharing between customers
- ✅ HTTPS encrypted
- ✅ Your content stays private

---

## 📱 Widget Features

- **Floating bubble** - Appears bottom-right (customizable)
- **Mobile friendly** - Works on phones and tablets
- **No conflicts** - Shadow DOM prevents CSS issues
- **Real-time** - Instant responses
- **Beautiful** - Gradient design
- **Accessible** - Works for everyone

---

## 🚀 Quick Start

1. **Get widget code** → From admin
2. **Copy the code** → 2 lines of JavaScript
3. **Paste on site** → Into your HTML
4. **Done** → Chat bubble appears automatically ✅



---

## 💡 Perfect For

- 🛒 E-commerce stores
- 📚 Documentation sites
- 🏢 Corporate websites
- 💼 Service businesses
- 📰 News sites
- 🎓 Education platforms
- 🏥 Healthcare providers
- 🍕 Restaurants

---

## 🎯 The Goal

**Make AI support so easy that every website can have it.**

One URL → One button → One line of code → Done.

---

**Transform your website into an AI-powered support machine** 🚀

