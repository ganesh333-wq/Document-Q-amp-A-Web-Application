# FastAPI - Complete Guide

## 🚀 What is FastAPI?

FastAPI is a modern Python web framework for building APIs (REST/JSON services). It's:
- **Fast:** High performance, comparable to Node.js and Go
- **Easy:** Intuitive syntax with auto-validation
- **Async-ready:** Built-in async/await support
- **Auto-documented:** Automatic interactive API docs

## 🏗️ FastAPI in This Project

This project uses FastAPI to create a backend server with **3 API endpoints**:

### Endpoint 1: Upload Document
```
POST /upload
```
Accepts a `.txt` file and returns document metadata

### Endpoint 2: Ask Question  
```
POST /ask
```
Accepts a question and document ID, returns an answer

### Endpoint 3: Health Check
```
GET /health
```
Returns API status and model information

---

## 🔌 How to Access FastAPI

### 1. **Web Browser (for GET requests)**

Once the backend is running on `http://localhost:8000`, you can access:

#### Health Check in Browser:
```
http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "llm_model": "llama-3.3-70b-versatile",
  "embedding_model": "all-MiniLM-L6-v2"
}
```

---

### 2. **Interactive API Documentation (Auto-generated)**

FastAPI automatically creates interactive documentation:

#### **Swagger UI** (Recommended)
```
http://localhost:8000/docs
```

Features:
- ✅ See all endpoints
- ✅ Try endpoints directly in browser
- ✅ See request/response schemas
- ✅ Auto-validation

#### **ReDoc** (Alternative)
```
http://localhost:8000/redoc
```

---

### 3. **JavaScript/Frontend (fetch API)**

```javascript
// Upload document
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/upload', {
  method: 'POST',
  body: formData
})
.then(res => res.json())
.then(data => console.log(data));
```

---

### 4. **Command Line (curl)**

#### Upload a document:
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test.txt"
```

Response:
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "test.txt",
  "total_chunks": 15
}
```

#### Ask a question:
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "What is the main topic?"
  }'
```

Response:
```json
{
  "answer": "The main topic is...",
  "sources": [0, 2, 5]
}
```

#### Health check:
```bash
curl "http://localhost:8000/health"
```

---

## 📂 FastAPI Project Structure

```
backend/
├── main.py              ← FastAPI app with endpoints
│                          - Creates app = FastAPI()
│                          - Defines routes: @app.post(), @app.get()
│                          - Enables CORS middleware
│                          - Handles HTTP requests/responses
│
├── rag.py               ← Business logic (embedding, retrieval)
│                          - Called by main.py endpoints
│                          - No HTTP handling
│
├── models.py            ← Pydantic schemas for validation
│                          - Request/response data validation
│                          - Automatic JSON serialization
│
└── requirements.txt     ← Dependencies
                           - fastapi
                           - uvicorn (ASGI server)
```

---

## 🔄 How FastAPI Handles Requests

### Request Flow:

```
1. User sends HTTP request
   ↓
2. ASGI Server (Uvicorn) receives request
   ↓
3. FastAPI routes to correct endpoint
   ↓
4. Request data validated against Pydantic model
   ↓
5. Endpoint handler function executes
   ↓
6. Response object created
   ↓
7. Response serialized to JSON
   ↓
8. HTTP response sent to client
```

### Example:

```python
@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    # 1. request: AskRequest is validated against Pydantic model
    # 2. If invalid, FastAPI returns 422 error automatically
    # 3. If valid, function executes
    # 4. Return response: AskResponse is serialized to JSON
    
    if not request.question.strip():
        raise HTTPException(400, "Question is empty")
    
    answer = "Answer based on document"
    sources = [0, 1, 2]
    
    return AskResponse(answer=answer, sources=sources)
    # Automatically converted to JSON and sent
```

---

## 🛡️ Key FastAPI Features Used

### 1. **Auto-Validation with Pydantic**

```python
from pydantic import BaseModel

class AskRequest(BaseModel):
    document_id: str
    question: str

# FastAPI validates JSON against this model
# ❌ Missing field? → 422 error
# ✅ All fields present? → Proceeds
```

### 2. **Async/Await (Non-blocking)**

```python
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # async = non-blocking
    # Can handle multiple requests simultaneously
    # await = pause until file is read
    content = await file.read()
```

### 3. **CORS Middleware**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)
# Allows frontend to make requests from different domain
```

### 4. **HTTP Status Codes**

```python
raise HTTPException(
    status_code=400,           # Bad Request
    detail="File is empty"
)

raise HTTPException(
    status_code=404,           # Not Found
    detail="Document not found"
)

raise HTTPException(
    status_code=503,           # Service Unavailable
    detail="LLM call failed"
)
```

---

## 🚀 Starting FastAPI Server

### Development Mode (with auto-reload):
```bash
python -m uvicorn main:app --reload --port 8000
```

### Production Mode:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Check Logs:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started server process [16314]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## 📊 API Response Types

### Success Response (200)
```json
{
  "document_id": "uuid",
  "filename": "test.txt",
  "total_chunks": 15
}
```

### Error Response (4xx)
```json
{
  "detail": "File is empty"
}
```

### Error Response (5xx)
```json
{
  "detail": "LLM call failed: ..."
}
```

---

## 🔍 Debugging FastAPI

### Check if running:
```bash
lsof -i :8000  # See what's on port 8000
```

### View request logs:
```
INFO:     127.0.0.1:54553 - "POST /upload HTTP/1.1" 200 OK
ERROR:    Exception in ASGI application
```

### Test endpoint:
```bash
curl -X GET "http://localhost:8000/health"
```

---

## 📚 FastAPI vs Other Frameworks

| Feature | FastAPI | Flask | Django |
|---------|---------|-------|--------|
| Speed | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Async | ✅ Built-in | ⚠️ Add-on | ⚠️ Add-on |
| Auto-docs | ✅ Yes | ❌ No | ❌ No |
| Validation | ✅ Pydantic | ⚠️ Manual | ✅ ORM |
| Learning Curve | Easy | Easy | Steep |

---

## 🎯 Key Takeaways

1. **FastAPI creates REST APIs** - HTTP endpoints that accept/return JSON
2. **Accessible via:**
   - Browser (GET requests, /docs)
   - fetch() in JavaScript
   - curl commands
   - HTTP clients (Postman, Insomnia)
3. **Auto-documentation at `/docs`**
4. **Automatic validation** using Pydantic models
5. **Async by default** for high performance
6. **CORS enabled** so frontend can call backend

---

**FastAPI is used for the entire backend infrastructure of this project!**
