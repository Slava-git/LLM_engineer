import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import datetime
import uuid

from .api import api_router
from .models.note import Note
from .storage import storage
from .search import vector_search
from .config import logger, app_config


app = FastAPI(
    title=app_config.title,
    version=app_config.version,
    description=app_config.description,
    openapi_url=app_config.openapi_url,
    docs_url=app_config.docs_url,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health_check():
    """Check if the API is healthy"""
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}

@app.get("/status", tags=["health"])
async def check_status():
    """Check status of the application components"""
    note_count = len(storage.get_all_notes())
    
    doc_count = vector_search.document_store.count_documents()
    
    notes_preview = [
        {"id": note.id, "content_preview": note.content[:100], "tags": note.tags}
        for note in storage.get_recent_notes(5)
    ]
    
    return {
        "status": "healthy",
        "storage": {
            "note_count": note_count,
            "notes_preview": notes_preview
        },
        "document_store": {
            "doc_count": doc_count
        },
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


@app.on_event("startup")
async def add_demo_notes():
    """Add demo notes for testing"""
    existing_notes = storage.get_all_notes()
    if existing_notes:
        logger.info(f"Skipping demo notes creation, found {len(existing_notes)} existing notes")
        return
        
    from .processing import note_processor
    
    demo_notes = [
        "Dentist appointment on Monday at 10:00",
        "Recipe for Sunday's pasta dinner: 8 cups of pasta, 12 cups of water, olive oil, salt, onions, garlic, Italian seasoning",
        "TODO: Check articles about LLMs with Memory",
        "#portuguese sorrir - to smile",
        "Weekend plans: Visit the farmers market on Saturday morning, then hike at Eagle Mountain",
        "Interesting LLM paper: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "Grocery list for Friday: avocados, cherry tomatoes, feta cheese, spinach, lemon juice",
        "Meeting with project team on Tuesday at 2:30 PM",
        "Interesting AI concept: Chain-of-Thought prompting in large language models"
    ]
    
    for i, content in enumerate(demo_notes):
        try:
            note = await note_processor.process_note(
                note_content=content
            )
            
            logger.info(f"Added demo note: {note.id}")
        except Exception as e:
            logger.error(f"Error adding demo note: {str(e)}")
    
    logger.info(f"Added {len(demo_notes)} demo notes")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)