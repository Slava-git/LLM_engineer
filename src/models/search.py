from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from .note import NoteResponse

class QueryRequest(BaseModel):
    """Request model for search queries"""
    query: str
    top_k: int = 5


class QueryResponse(BaseModel):
    """Response model for search results"""
    results: List[NoteResponse]
    total_results: int


class QARequest(BaseModel):
    """Request model for question-answering"""
    query: str
    top_k: int = 5


class QAResponse(BaseModel):
    """Response model for question-answering"""
    answer: str
    documents: List[NoteResponse]


class TagSearchRequest(BaseModel):
    """Request model for tag search"""
    tags: List[str]
    limit: int = 10