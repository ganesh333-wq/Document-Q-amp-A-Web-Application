# How Document Q&A Web Application Works

## 🎯 Overview

This is a **Retrieval-Augmented Generation (RAG)** system that answers questions based ONLY on uploaded document content, without using the LLM's general knowledge. This prevents hallucinations and ensures accuracy.

## 🔄 Complete Flow

### Phase 1: Document Upload (POST /upload)

```
1. User selects .txt file from browser
   ↓
2. Frontend sends file to backend via multipart/form-data
   ↓
3. Backend (main.py) receives file and validates:
   - Is it a .txt file? ✓
   - Is it not empty? ✓
   ↓
4. RAG System chunks the document:
   - Text: "Python is a programming language. It was created in 1991..."
   - Chunk 1: "Python is a programming language. It was created in" (300 chars)
   - Chunk 2: "created in 1991 by Guido van Rossum. Python is known for" (300 chars)
   - Note: 50-character overlap between chunks for context preservation
   ↓
5. Each chunk gets embedded using all-MiniLM-L6-v2:
   - Chunk 1 → [0.123, -0.456, 0.789, ...] (384 dimensions)
   - Chunk 2 → [0.124, -0.450, 0.785, ...] (384 dimensions)
   - Chunk N → [0.120, -0.460, 0.790, ...] (384 dimensions)
   ↓
6. Chunks + embeddings stored in in-memory dictionary:
   {
     "document_id_xyz": {
       "filename": "example.txt",
       "chunks": ["Chunk 1 text", "Chunk 2 text", ...],
       "embeddings": [[0.123, -0.456, ...], [0.124, -0.450, ...], ...]
     }
   }
   ↓
7. Backend returns to frontend:
   {
     "document_id": "550e8400-e29b-41d4-a716-446655440000",
     "filename": "example.txt",
     "total_chunks": 15
   }
   ↓
8. Frontend displays success message and enables Q&A section
```

**Key Technology: all-MiniLM-L6-v2**
- Converts text to 384-dimensional vectors
- Similar text has similar embeddings (vectors close in space)
- Used for finding relevant chunks quickly

### Phase 2: Question Asking (POST /ask)

```
1. User types question: "What year was Python created?"
   ↓
2. Frontend sends to backend:
   {
     "document_id": "550e8400-e29b-41d4-a716-446655440000",
     "question": "What year was Python created?"
   }
   ↓
3. Backend embeds the question using all-MiniLM-L6-v2:
   "What year was Python created?" → [0.125, -0.455, 0.788, ...]
   ↓
4. RAG System calculates similarity between question embedding and ALL chunk embeddings
   using COSINE SIMILARITY:
   
   cosine_similarity = (A · B) / (|A| × |B|)
   
   Where:
   - A = question embedding [0.125, -0.455, 0.788, ...]
   - B = chunk embedding [0.123, -0.456, 0.789, ...]
   
   Similarities:
   - Chunk 1: 0.95 ✓ (very similar!)
   - Chunk 2: 0.88 ✓ (similar)
   - Chunk 3: 0.92 ✓ (very similar!)
   - Chunk 4: 0.42 (not similar)
   - Chunk 5: 0.38 (not similar)
   ↓
5. Retrieve TOP-3 chunks by similarity:
   1. Chunk 1 (similarity: 0.95)
   2. Chunk 3 (similarity: 0.92)
   3. Chunk 2 (similarity: 0.88)
   ↓
6. Build CONTEXT from top-3 chunks:
   
   Context = 
   "[Chunk 1]: Python is a programming language created in 1991
    [Chunk 3]: Created by Guido van Rossum, Python is known for...
    [Chunk 2]: Python has simple syntax and is widely used..."
   ↓
7. Send to Groq LLM with CONSTRAINED SYSTEM PROMPT:
   
   System Prompt:
   "You are a helpful assistant that answers questions based ONLY 
    on the provided document context.
    
    IMPORTANT:
    1. Answer ONLY based on the context given
    2. If info is NOT in the context, say 'Not in document'
    3. Do NOT use general knowledge
    4. Never make up information
    
    Context:
    [Chunk 1]: Python is a programming language created in 1991...
    [Chunk 3]: Created by Guido van Rossum...
    [Chunk 2]: Python has simple syntax...
    
    User Question: What year was Python created?"
   ↓
8. Groq LLM generates answer:
   
   Response:
   "According to the document, Python was created in 1991."
   ↓
9. Backend returns to frontend:
   {
     "answer": "According to the document, Python was created in 1991.",
     "sources": [1, 3, 2]  ← Chunk indices used
   }
   ↓
10. Frontend displays:
    - Answer text
    - Source chunk numbers: "Sources: Chunks 1, 3, 2"
    - Green success message
```

## 🧮 Key Concepts Explained

### 1. Embeddings (Vector Representations)

**What:** Converting text to numbers that capture meaning

```
Text:  "Python is a programming language"
       ↓ (all-MiniLM-L6-v2)
Vector: [0.123, -0.456, 0.789, ..., 0.234]
        (1536 dimensions)
```

**Why:** 
- Numbers can be compared mathematically
- Similar texts have similar embeddings
- Fast to search through many embeddings

### 2. Chunking (Breaking Text Into Pieces)

**Why split documents?**
- LLMs have token limits
- Easier to find relevant info in smaller pieces
- Better context preservation

**Strategy Used:**
- Chunk size: 300 characters
- Overlap: 50 characters (for context between chunks)

```
Original: "Python is great. It was created in 1991. It is widely used."

Chunk 1: "Python is great. It was created in 1991. It is wide"
Chunk 2: "in 1991. It is widely used. Python has many libraries."
         ↑ 50-char overlap for context ↑
```

### 3. Cosine Similarity (Finding Relevance)

**Formula:**
```
similarity = dot_product(vec1, vec2) / (magnitude(vec1) × magnitude(vec2))

Result: Number between 0 and 1
- 1.0 = identical
- 0.5 = somewhat similar
- 0.0 = completely different
```

**Example:**
```
Question: "When was Python made?"
Question embedding: [0.125, -0.455, 0.788, ...]

Chunk 1: "Python created in 1991"
Chunk 1 embedding: [0.123, -0.456, 0.789, ...]
Similarity: 0.95 (VERY SIMILAR!)

Chunk 5: "Python has great error messages"
Chunk 5 embedding: [0.234, -0.123, 0.456, ...]
Similarity: 0.42 (less similar)
```

### 4. System Prompt Constraint (Preventing Hallucination)

**Without constraint:**
```
User: "What year was Python created?"
LLM: "Python was created in 1991." ← Could use general knowledge
Document: "..."  ← Might not mention year at all!
```

**With constraint:**
```
System: "Answer ONLY from provided context. If not mentioned, say so."
User: "What year was Python created?"
Context: "..." (no year mentioned)
LLM: "This information is not available in the document."
     ✓ Correct! Won't hallucinate
```

## 📊 Example Walkthrough

### Upload Example

**Input File (test.txt):**
```
The Earth is the third planet from the Sun.
It is approximately 4.54 billion years old.
The Moon orbits Earth every 27.3 days.
```

**Processing:**
```
Step 1: Chunk text (300 chars + 50 overlap)
  Chunk 0: "The Earth is the third planet from the Sun. It is approximately 4.54 billion years old."
  Chunk 1: "old. The Moon orbits Earth every 27.3 days."

Step 2: Embed each chunk
  Chunk 0 → [0.101, -0.234, 0.567, ..., 0.890]
  Chunk 1 → [0.102, -0.233, 0.568, ..., 0.891]

Step 3: Store
  document_id = "abc-123-def"
  documents_store["abc-123-def"] = {
    "filename": "test.txt",
    "chunks": ["The Earth is...", "old. The Moon..."],
    "embeddings": [[0.101, -0.234, ...], [0.102, -0.233, ...]]
  }

Response:
  {
    "document_id": "abc-123-def",
    "filename": "test.txt",
    "total_chunks": 2
  }
```

### Question Example

**User Question:** "How old is the Earth?"

**Processing:**
```
Step 1: Embed question
  "How old is the Earth?" → [0.103, -0.235, 0.569, ...]

Step 2: Calculate similarities
  vs Chunk 0: cosine_sim([0.103, -0.235, ...], [0.101, -0.234, ...]) = 0.94 ✓ TOP
  vs Chunk 1: cosine_sim([0.103, -0.235, ...], [0.102, -0.233, ...]) = 0.52

Step 3: Get top-3 (but we only have 2)
  Top chunks: [Chunk 0, Chunk 1]

Step 4: Build context
  Context = "The Earth is the third planet from the Sun. It is 
             approximately 4.54 billion years old. The Moon orbits 
             Earth every 27.3 days."

Step 5: Call Groq LLM
  System Prompt: "Answer from context only. If not in document, say so."
  Context: "The Earth is... approximately 4.54 billion years old..."
  Question: "How old is the Earth?"

  Response: "According to the document, the Earth is approximately 
            4.54 billion years old."

Step 6: Return answer
  {
    "answer": "According to the document, the Earth is approximately 4.54 billion years old.",
    "sources": [0, 1]
  }
```

## 🛡️ Safety Features

### 1. Document-Only Constraint
- System prompt explicitly forbids using general knowledge
- Forces LLM to answer from context or say "not in document"

### 2. Source Attribution
- Every answer comes with chunk indices
- Users can verify answers by looking at source chunks

### 3. Error Handling
- 400: Empty file or empty question
- 404: Document ID not found
- 415: Wrong file type (not .txt)
- 503: API failure

### 4. Efficient Retrieval
- Only sends top-3 chunks to LLM
- Saves API tokens and costs
- Faster response times

## 💰 Cost Breakdown

### Per Upload (500KB file, 50 chunks)
- Embeddings: Free local Sentence Transformers processing

### Per Question
- Question embedding: Free local Sentence Transformers processing
- LLM response: Uses Groq API free tier/pricing

## 🚀 Scaling Considerations

### For Production:

1. **Database Storage**
   - Replace in-memory with PostgreSQL + pgvector
   - Persist embeddings for long-term use
   - Handle large document collections

2. **Caching**
   - Cache embeddings to avoid re-computing
   - Cache common question responses
   - Reduce API calls

3. **Better Retrieval**
   - Use FAISS or Pinecone for fast vector search
   - Hybrid search (keyword + semantic)
   - Re-ranking algorithms

4. **Load Balancing**
   - Multiple API server instances
   - Queue for async processing
   - Rate limiting

---

**This system combines the best of both worlds: semantic understanding from embeddings + factual accuracy from document retrieval!**
