from typing import List
from fastapi import APIRouter, HTTPException
from ..models.tag import TagProcessRequest, TagProcessResponse
from ..storage import storage
from ..search import tag_vector_store
from ..config import logger

router = APIRouter(prefix="/tags", tags=["tags"])

@router.get("", response_model=List[str])
async def get_all_tags():
    """Get all tags"""
    tags = storage.get_all_tags()
    logger.info(f"Retrieved {len(tags)} tags")
    return tags

@router.post("/process", response_model=TagProcessResponse)
async def process_tag(request: TagProcessRequest):
    """Process a tag through tag vector store"""
    logger.info(f"Processing tag: {request.tag}")
    
    result = tag_vector_store.run(tag=request.tag)
    
    return {
        "original_tag": request.tag,
        "processed_tag": result["processed_tag"],
        "is_new": result["is_new"]
    }