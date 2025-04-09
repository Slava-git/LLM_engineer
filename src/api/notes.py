from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from ..models.note import Note, NoteCreate, NoteUpdate, NoteResponse, NoteList
from ..storage import storage
from ..processing import note_processor
from ..config import logger


router = APIRouter(prefix="/notes", tags=["notes"])

@router.post("", response_model=NoteResponse, status_code=201)
async def create_note(note_data: NoteCreate):
    """Create a new note"""
    logger.info(f"Creating note: {note_data.content[:50]}...")
    
    note = await note_processor.process_note(
        note_content=note_data.content,
        tags=note_data.tags
    )
    
    return note

@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str):
    """Get a specific note by ID"""
    note = storage.get_note(note_id)
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return note

@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(note_id: str, note_data: NoteUpdate):
    """Update a note"""
    updated_note = await note_processor.update_note(
        note_id=note_id,
        content=note_data.content,
        tags=note_data.tags
    )
    
    if not updated_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return updated_note

@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: str):
    """Delete a note"""
    note = storage.get_note(note_id)
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    storage.delete_note(note_id)
    
    from ..search import vector_search
    vector_search.delete_from_index(note_id)

@router.get("", response_model=NoteList)
async def list_notes(limit: int = Query(10, ge=1, le=100)):
    """Get recent notes"""
    notes = storage.get_recent_notes(limit)
    return {"notes": notes, "total": len(notes)}