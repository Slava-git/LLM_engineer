from typing import Dict, List, Optional, Any
import datetime
from .base import BaseStorage
from ..models.note import Note
from ..config import logger

class InMemoryStorage(BaseStorage):
    """Simple in-memory storage implementation"""
    
    def __init__(self):
        """Initialize in-memory storage"""
        self.notes: List[Note] = []
        self.tags: Dict[str, Dict[str, Any]] = {}
    
    def save_note(self, note: Note) -> Note:
        """Save or update a note"""
        for i, existing_note in enumerate(self.notes):
            if existing_note.id == note.id:
                note.created_at = existing_note.created_at
                note.updated_at = datetime.datetime.now().isoformat()
                self.notes[i] = note
                
                self._save_note_tags(note.tags)
                
                return note
        
        self.notes.append(note)
        
        self._save_note_tags(note.tags)
        
        return note
    
    def get_note(self, note_id: str) -> Optional[Note]:
        """Get note by ID"""
        for note in self.notes:
            if note.id == note_id:
                return note
        return None
    
    def delete_note(self, note_id: str) -> bool:
        """Delete note by ID"""
        initial_count = len(self.notes)
        self.notes = [note for note in self.notes if note.id != note_id]
        return len(self.notes) < initial_count
    
    def get_all_notes(self) -> List[Note]:
        """Get all notes"""
        return self.notes
    
    def get_recent_notes(self, limit: int = 10) -> List[Note]:
        """Get most recent notes"""
        sorted_notes = sorted(self.notes, key=lambda x: x.created_at, reverse=True)
        return sorted_notes[:limit]
    
    def search_notes_by_tags(self, tags: List[str]) -> List[Note]:
        """Search notes by tags"""
        results = []
        for note in self.notes:
            if any(tag in note.tags for tag in tags):
                results.append(note)
        return results
    
    def save_tag(self, tag_name: str) -> None:
        """Save a tag to storage"""
        if tag_name not in self.tags:
            now = datetime.datetime.now().isoformat()
            self.tags[tag_name] = {
                "name": tag_name,
                "created_at": now,
                "updated_at": now
            }
        else:
            self.tags[tag_name]["updated_at"] = datetime.datetime.now().isoformat()
    
    def get_all_tags(self) -> List[str]:
        """Get all tags"""
        return list(self.tags.keys())
    
    def _save_note_tags(self, tags: List[str]) -> None:
        """Save tags from a note"""
        for tag in tags:
            self.save_tag(tag)