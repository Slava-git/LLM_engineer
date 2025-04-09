from fastapi import APIRouter, HTTPException
from ..models.search import QARequest, QAResponse
from ..processing import rag_pipeline
from ..config import logger, OPENAI_API_KEY

router = APIRouter(prefix="/qa", tags=["qa"])

@router.post("", response_model=QAResponse)
async def answer_question(request: QARequest):
    """Answer a question using RAG"""
    
    if not OPENAI_API_KEY or rag_pipeline is None:
        raise HTTPException(
            status_code=501, 
            detail="Question answering is not available - OpenAI API key not configured"
        )
    
    logger.info(f"QA request: {request.query}, top_k={request.top_k}")
    
    result = await rag_pipeline.answer_question(
        query=request.query,
        top_k=request.top_k
    )
    
    logger.info(f"Generated answer of length {len(result['answer'])}")
    
    return result