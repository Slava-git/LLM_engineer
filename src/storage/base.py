from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from ..models.note import Note

class BaseStorage(ABC):
    """Abstract base class for storage implementations"""
    
    @abstractmethod
    def save_note(self, note: Note) -> Note:
        """Save a note to storage"""
        pass
    
    @abstractmethod
    def get_note(self, note_id: str) -> Optional[Note]:
        """Get a note from storage by ID"""
        pass
    
    @abstractmethod
    def delete_note(self, note_id: str) -> bool:
        """Delete a note from storage by ID"""
        pass
    
    @abstractmethod
    def get_all_notes(self) -> List[Note]:
        """Get all notes from storage"""
        pass
    
    @abstractmethod
    def get_recent_notes(self, limit: int = 10) -> List[Note]:
        """Get most recent notes from storage"""
        pass
    
    @abstractmethod
    def search_notes_by_tags(self, tags: List[str]) -> List[Note]:
        """Search notes by tags"""
        pass
    
    @abstractmethod
    def save_tag(self, tag_name: str) -> None:
        """Save a tag to storage"""
        pass
    
    @abstractmethod
    def get_all_tags(self) -> List[str]:
        """Get all tags from storage"""
        pass