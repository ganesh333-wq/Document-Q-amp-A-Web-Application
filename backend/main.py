"""
FastAPI Backend for Document Q&A Web Application
Implements: /upload, /ask, /health endpoints
Using Groq for LLM and Sentence Transformers for embeddings
"""
import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from models import UploadResponse, AskRequest, AskResponse, HealthResponse
from rag import (
    chunk_text,
    embed_chunks,
    save_document,
    retrieve_relevant_chunks,
    document_exists,
)

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Document Q&A API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
LLM_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50
FRONTEND_INDEX = Path(__file__).resolve().parent.parent / "frontend" / "index.html"

QA_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a helpful assistant that answers questions based ONLY on the provided document context.

IMPORTANT RULES:
1. Answer ONLY based on the document content provided
2. If the answer is not in the document, clearly state: "This information is not available in the document."
3. Do NOT use your general knowledge
4. If asked something not in the document, politely refuse to answer
5. Cite which chunks (by number) you used for your answer

Document Context:
{context}"""
    ),
    ("human", "{question}"),
])

# LangChain owns the chatbot prompt and answer-generation pipeline.
qa_chain = (
    QA_PROMPT
    | ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model=LLM_MODEL,
        temperature=0.7,
        max_tokens=500,
    )
    | StrOutputParser()
)


@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Serve the single-page frontend from the hosted API origin."""
    return FileResponse(FRONTEND_INDEX)


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a text file, chunk it, and embed the chunks
    
    Args:
        file: .txt file to upload
    
    Returns:
        Document ID, filename, and total chunks count
    """
    # Validate file type
    if not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only .txt files are supported"
        )
    
    # Read file content
    content = await file.read()
    text = content.decode("utf-8")
    
    # Validate file is not empty
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )
    
    # Chunk the text
    chunks = chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    
    # Embed chunks
    embeddings = embed_chunks(chunks)
    
    # Save document
    doc_id = save_document(file.filename, chunks, embeddings)
    
    return UploadResponse(
        document_id=doc_id,
        filename=file.filename,
        total_chunks=len(chunks)
    )


@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Ask a question about an uploaded document
    
    Args:
        request: Contains document_id and question
    
    Returns:
        Answer based on document context and source chunk indices
    """
    # Validate question
    if not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question is empty"
        )
    
    # Check if document exists
    if not document_exists(request.document_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Retrieve relevant chunks
    relevant_chunks, chunk_indices = retrieve_relevant_chunks(
        request.question,
        request.document_id,
        top_k=3
    )
    
    if not relevant_chunks:
        return AskResponse(
            answer="No relevant information found in the document.",
            sources=[]
        )
    
    # Build context from relevant chunks
    context = "\n\n".join([
        f"[Chunk {idx}]: {chunk}"
        for idx, chunk in zip(chunk_indices, relevant_chunks)
    ])
    
    try:
        answer = qa_chain.invoke({
            "context": context,
            "question": request.question,
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM call failed: {str(e)}"
        )
    
    return AskResponse(
        answer=answer,
        sources=chunk_indices
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check API health and return model information
    """
    return HealthResponse(
        status="healthy",
        llm_model=LLM_MODEL,
        embedding_model=EMBEDDING_MODEL
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
