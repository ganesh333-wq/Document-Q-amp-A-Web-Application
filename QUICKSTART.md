# Quick Start Guide

## ⚡ Get Running in 5 Minutes

### Step 1: Get Groq API Key
1. Go to [Groq Console](https://console.groq.com/keys)
2. Create a new API key
3. Copy it

### Step 2: Setup Backend

```bash
# Navigate to backend
cd backend

# Create .env file
echo "GROQ_API_KEY=gsk-your-key-here" > .env

# Install dependencies
pip install -r requirements.txt

# Start server
python -m uvicorn main:app --reload
```

You'll see:
```
Uvicorn running on http://127.0.0.1:8000
```

### Step 3: Open Frontend

```bash
# Option 1: Direct file opening (simplest)
open frontend/index.html

# Option 2: With HTTP server
python -m http.server 8001 --directory frontend
# Visit http://localhost:8001
```

### Step 4: Test It!

1. Create a test file `test.txt`:
```
Python is a programming language created by Guido van Rossum.
It was first released in 1991.
Python is known for its simple and readable syntax.
```

2. In the web UI:
   - Click "Select a .txt file" and choose `test.txt`
   - Click "Upload Document"
   - Type: "When was Python created?"
   - Click "Ask Question"

3. Expected Answer: "1991" or similar, with source chunks shown

---

## 🔍 API Testing with curl

### Upload Document
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test.txt"
```

### Ask Question
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "When was Python created?"
  }'
```

### Health Check
```bash
curl "http://localhost:8000/health"
```

---

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'fastapi'` | Run `pip install -r requirements.txt` |
| `GROQ_API_KEY not found` | Create `backend/.env` with your key |
| `Connection refused on port 8000` | Make sure backend is running |
| `CORS error in browser` | Backend has CORS enabled, ensure correct URL |

---

## 📊 How the System Works

```
┌─────────────────────────────────────────┐
│          User Uploads File              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Split into 300-char chunks with 50    │
│  character overlap                      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Embed each chunk using                │
│  all-MiniLM-L6-v2                     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Store chunks + embeddings              │
│  Return document_id                     │
└─────────────────────────────────────────┘

────────────────────────────────────────

┌─────────────────────────────────────────┐
│      User Asks a Question               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Embed the question                     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Find 3 most similar chunks using       │
│  cosine similarity                      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Send chunks + question to Groq LLM     │
│  with "answer only from context"        │
│  constraint                             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Return answer + source chunk indices   │
└─────────────────────────────────────────┘
```

---

**Ready? Start with Step 1! 🚀**
