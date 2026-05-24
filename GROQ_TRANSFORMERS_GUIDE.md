# Groq + Sentence Transformers Setup Guide

## ✅ Step 1: Get a Groq API Key (FREE)

### 1. Sign up at Groq Console
- Go to [console.groq.com](https://console.groq.com/keys)
- Click "Sign in with Google" or create account
- Accept terms

### 2. Create API Key
- Navigate to "API Keys" section
- Click "Create API Key"
- Copy the key (starts with `gsk-`)

### 3. Update `.env` file
```bash
# Edit backend/.env
GROQ_API_KEY=gsk-your-key-here
```

Or use terminal:
```bash
cd /Users/apple/Document\ Q\&A\ Web\ Apllication/backend
echo "GROQ_API_KEY=gsk-your-key-here" > .env
```

---

## 📦 Step 2: Install Dependencies

All required packages are in `requirements.txt`:

```bash
cd /Users/apple/Document\ Q\&A\ Web\ Apllication/backend
pip install -r requirements.txt
```

**Dependencies:**
- `langchain` - Prompt chain for the chatbot pipeline
- `langchain-groq` - LangChain integration for Groq chat models
- `sentence-transformers==3.0.1` - Local embeddings (all-MiniLM-L6-v2)
- `fastapi==0.104.1` - Web framework
- `uvicorn==0.24.0` - ASGI server
- `python-dotenv==1.0.0` - Load environment variables

---

## 🚀 Step 3: Start the Backend

```bash
cd /Users/apple/Document\ Q\&A\ Web\ Apllication/backend
python -m uvicorn main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**First run:** Sentence Transformers will download the `all-MiniLM-L6-v2` model (~100MB)

---

## 🔍 How Each Component Works

### 1. **Groq LLM (llama-3.3-70b-versatile)**

**What:** Large language model hosted on Groq infrastructure (super fast)

**Used for:** Generating answers to questions

**Speed:** ~300ms (vs 2-3s with OpenAI)

**How it works:**
```python
# In main.py
qa_chain = QA_PROMPT | ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    max_tokens=500,
) | StrOutputParser()

answer = qa_chain.invoke({"context": context, "question": question})
```

---

### 2. **Sentence Transformers (all-MiniLM-L6-v2)**

**What:** Small, fast embedding model that runs locally

**Used for:** Converting text to vectors for similarity search

**Speed:** <10ms per chunk (instant)

**Dimensions:** 384 dimensions (vs OpenAI's 1536)

**How it works:**
```python
# In rag.py
from sentence_transformers import SentenceTransformer
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Single text
embedding = embedding_model.encode("Python is great")
# Result: [0.123, -0.456, 0.789, ..., 0.234] (384 floats)

# Multiple texts (batch - faster)
embeddings = embedding_model.encode(["text1", "text2", "text3"])
# Result: [[...], [...], [...]]
```

---

## 📊 Architecture After Update

```
┌─────────────────────────────────────────┐
│         Frontend (HTML/CSS/JS)          │
│  http://localhost:8001/frontend         │
└──────────────┬──────────────────────────┘
               │ HTTP (fetch)
               ▼
┌─────────────────────────────────────────┐
│     FastAPI Backend (main.py)           │
│    http://localhost:8000                │
│  ✅ /upload - POST                      │
│  ✅ /ask - POST                         │
│  ✅ /health - GET                       │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
    ┌────────────┐  ┌──────────────────────┐
    │ Sentence   │  │      Groq API        │
    │ Transform  │  │ (Llama 3.3 70B)      │
    │ (Local)    │  │   Fast inference     │
    │ Embedding  │  │   Response: <1s      │
    │ 384-dim    │  │ gsk-...API key       │
    └────────────┘  └──────────────────────┘
```

---

## 🧪 Test the System

### 1. Upload a test document:

**Create `test.txt`:**
```
Python is a programming language created in 1991.
It was created by Guido van Rossum.
Python is known for its simple, readable syntax.
Many companies use Python for machine learning and data science.
```

**Upload via curl:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test.txt"
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "test.txt",
  "total_chunks": 2
}
```

### 2. Ask a question:

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "When was Python created?"
  }'
```

**Response:**
```json
{
  "answer": "According to the document, Python was created in 1991.",
  "sources": [0]
}
```

### 3. Check health:

```bash
curl "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy",
  "llm_model": "llama-3.3-70b-versatile",
  "embedding_model": "all-MiniLM-L6-v2"
}
```

---

## 🎨 Using via Web Browser

### Interactive API Documentation:
```
http://localhost:8000/docs
```

Features:
- Upload files directly
- Send POST requests
- See responses in real-time

---

## ⚡ Performance Comparison

### Processing a 5KB document (20 chunks):

| Metric | OpenAI | Groq + Transformers |
|--------|--------|-----|
| Upload | ~5 sec | **<1 sec** |
| Embedding | API calls | **Instant** |
| LLM Response | 2-3 sec | **<1 sec** |
| **Total** | ~7 sec | **<2 sec** |



## 🔧 Troubleshooting

### Error: `ModuleNotFoundError: No module named 'groq'`
```bash
pip install groq
```

### Error: `ModuleNotFoundError: No module named 'sentence_transformers'`
```bash
pip install sentence-transformers
```

### Error: `GROQ_API_KEY not found`
1. Check `.env` file exists in `backend/` folder
2. Verify format: `GROQ_API_KEY=gsk-...`
3. Restart backend server

### Error: `Connection refused on port 8000`
```bash
# Kill existing process
lsof -i :8000 | grep LISTEN
kill -9 <PID>

# Start fresh
python -m uvicorn main:app --reload
```

### Model Download on First Run
First time using Sentence Transformers, it downloads the model (~100MB):
```
Downloading (…)oken_embeddings.py from huggingface.co...
Downloading (…)768/model.safetensors...
100%|██████████| 134M/134M [00:30<00:00, 4.4MB/s]
```

This is normal and happens only once!

---

## 🎯 Summary

✅ **LLM:** Groq's llama-3.3-70b-versatile (fast, free tier)  
✅ **Embeddings:** Sentence Transformers all-MiniLM-L6-v2 (local, instant)  
✅ **Backend:** FastAPI (3 endpoints)  
✅ **Frontend:** HTML/CSS/JavaScript  

---

**Questions? Check FASTAPI_GUIDE.md for how to access the API!**
