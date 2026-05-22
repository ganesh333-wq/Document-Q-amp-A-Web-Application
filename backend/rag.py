"""
RAG (Retrieval-Augmented Generation) implementation
Handles chunking, embedding, and retrieval of document chunks
Using Groq for LLM and Sentence Transformers for embeddings
"""
import uuid
from typing import List, Optional, Tuple
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
embedding_model: Optional[SentenceTransformer] = None

# In-memory document storage (in production, use a database)
# Format: {document_id: {"filename": str, "chunks": [str], "embeddings": [[float]]}}
documents_store = {}


def get_embedding_model() -> SentenceTransformer:
    """Load the local embedding model on first use."""
    global embedding_model
    if embedding_model is None:
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return embedding_model


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: The text to chunk
        chunk_size: Size of each chunk (in characters)
        overlap: Overlap between chunks (in characters)
    
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        chunks.append(chunk.strip())
        
        # Move start position forward, accounting for overlap
        start = end - overlap if end < len(text) else end
    
    return [c for c in chunks if c]  # Remove empty chunks


def embed_text(text: str) -> List[float]:
    """
    Generate embeddings for a text using Sentence Transformers
    Uses all-MiniLM-L6-v2 model (local, free, fast)
    
    Args:
        text: Text to embed
    
    Returns:
        Embedding vector (384 dimensions)
    """
    embedding = get_embedding_model().encode(text, convert_to_tensor=False)
    return embedding.tolist()


def embed_chunks(chunks: List[str]) -> List[List[float]]:
    """
    Embed multiple chunks efficiently using batch processing
    
    Args:
        chunks: List of text chunks
    
    Returns:
        List of embedding vectors (384 dimensions each)
    """
    # Use batch encoding for better performance
    embeddings = get_embedding_model().encode(chunks, convert_to_tensor=False)
    return [emb.tolist() for emb in embeddings]


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    """
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a**2 for a in vec1) ** 0.5
    magnitude2 = sum(b**2 for b in vec2) ** 0.5
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
    
    return dot_product / (magnitude1 * magnitude2)


def retrieve_relevant_chunks(
    question: str, 
    document_id: str, 
    top_k: int = 3
) -> Tuple[List[str], List[int]]:
    """
    Retrieve the most relevant chunks for a question
    
    Args:
        question: The question to ask
        document_id: ID of the document to search in
        top_k: Number of top chunks to retrieve
    
    Returns:
        Tuple of (relevant_chunks, chunk_indices)
    """
    if document_id not in documents_store:
        return [], []
    
    doc = documents_store[document_id]
    chunks = doc["chunks"]
    embeddings = doc["embeddings"]
    
    # Get question embedding
    question_embedding = embed_text(question)
    
    # Calculate similarity scores
    similarities = [
        (idx, cosine_similarity(question_embedding, emb))
        for idx, emb in enumerate(embeddings)
    ]
    
    # Sort by similarity and get top-k
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_results = similarities[:top_k]
    
    # Return chunks and indices
    relevant_chunks = [chunks[idx] for idx, _ in top_results]
    chunk_indices = [idx for idx, _ in top_results]
    
    return relevant_chunks, chunk_indices


def save_document(filename: str, chunks: List[str], embeddings: List[List[float]]) -> str:
    """
    Save a document's chunks and embeddings
    
    Args:
        filename: Name of the file
        chunks: List of text chunks
        embeddings: List of embeddings
    
    Returns:
        Document ID
    """
    doc_id = str(uuid.uuid4())
    documents_store[doc_id] = {
        "filename": filename,
        "chunks": chunks,
        "embeddings": embeddings
    }
    return doc_id


def get_document(document_id: str) -> dict:
    """
    Retrieve a document from storage
    """
    return documents_store.get(document_id)


def document_exists(document_id: str) -> bool:
    """
    Check if a document exists
    """
    return document_id in documents_store
