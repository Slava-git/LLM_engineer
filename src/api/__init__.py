from fastapi import APIRouter
from .notes import router as notes_router
from .search import router as search_router
from .tags import router as tags_router
from .qa import router as qa_router

api_router = APIRouter()

api_router.include_router(notes_router)
api_router.include_router(search_router)
api_router.include_router(tags_router)
api_router.include_router(qa_router)