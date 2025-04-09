from typing import List
from fastapi import APIRouter, HTTPException, Query
from ..models.search import QueryRequest, QueryResponse, TagSearchRequest
from ..models.note import NoteResponse, NoteList
from ..storage import storage
from ..search import vector_search
from ..config import logger

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/vector", response_model=QueryResponse)
async def search_notes(query_req: QueryRequest):
    """Search notes using dense vector search"""
    logger.info(f"Vector search request: {query_req.query}, top_k={query_req.top_k}")
    
    results = vector_search.search(query_req.query, query_req.top_k)
    
    logger.info(f"Search returned {len(results)} results")
    
    return {
        "results": results,
        "total_results": len(results)
    }

@router.post("/tags", response_model=NoteList)
async def search_by_tags(search_req: TagSearchRequest):
    """Search notes by tags"""
    logger.info(f"Tag search request: {search_req.tags}")
    
    results = storage.search_notes_by_tags(search_req.tags)
    
    if search_req.limit and search_req.limit < len(results):
        results = results[:search_req.limit]
    
    logger.info(f"Tag search returned {len(results)} results")
    
    return {
        "notes": results,
        "total": len(results)
    }

@router.get("/tags", response_model=List[str])
async def get_all_tags():
    """Get all tags"""
    tags = storage.get_all_tags()
    return tags