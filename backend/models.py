"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel
from typing import List, Optional


class UploadResponse(BaseModel):
    """Response after uploading a document"""
    document_id: str
    filename: str
    total_chunks: int


class AskRequest(BaseModel):
    """Request to ask a question about a document"""
    document_id: str
    question: str


class AskResponse(BaseModel):
    """Response to a question"""
    answer: str
    sources: List[int]


class HealthResponse(BaseModel):
    """API health status"""
    status: str
    llm_model: str
    embedding_model: str
