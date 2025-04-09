from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import datetime
import uuid
from haystack.dataclasses import Document

class Note(BaseModel):
    """Note data model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    tags: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Dentist appointment on Monday at 10:00",
                "tags": ["appointment", "health"],
                "metadata": {
                    "structured_data": {
                        "title": "Dentist Appointment",
                        "date": "Monday",
                        "time": "10:00"
                    },
                    "structure_type": "appointment",
                    "confidence": 0.95
                }
            }
        }
    
    def to_haystack_document(self) -> Document:
        """Convert to Haystack Document"""
        meta = {
            "id": self.id,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        
        if self.metadata:
            meta["metadata"] = self.metadata
            
        return Document(
            content=self.content,
            meta=meta,
            id=self.id,
        )
    
    @classmethod
    def from_haystack_document(cls, doc: Document) -> "Note":
        """Create Note from Haystack Document"""
        metadata = {}
        if "metadata" in doc.meta:
            metadata = doc.meta.get("metadata", {})
            
        return cls(
            id=doc.id,
            content=doc.content,
            tags=doc.meta.get("tags", []),
            created_at=doc.meta.get("created_at", ""),
            updated_at=doc.meta.get("updated_at", ""),
            metadata=metadata
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Note":
        """Create Note from dictionary (for MongoDB storage)"""
        note_dict = {
            "id": data.get("id", str(uuid.uuid4())),
            "content": data.get("content", ""),
            "tags": data.get("tags", []),
            "created_at": data.get("created_at", datetime.datetime.now().isoformat()),
            "updated_at": data.get("updated_at", datetime.datetime.now().isoformat()),
        }
        
        # Handle metadata
        if "metadata" in data:
            note_dict["metadata"] = data["metadata"]
        elif "structured_data" in data:
            # For backward compatibility
            note_dict["metadata"] = {
                "structured_data": data.get("structured_data", {}),
                "structure_type": data.get("structure_type", "unknown"),
                "confidence": data.get("confidence", 0.0)
            }
            
        return cls(**note_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for MongoDB storage)"""
        return self.model_dump()


class NoteCreate(BaseModel):
    """Request model for creating a note"""
    content: str
    tags: Optional[List[str]] = None


class NoteUpdate(BaseModel):
    """Request model for updating a note"""
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class NoteResponse(BaseModel):
    """Response model for notes"""
    id: str
    content: str
    tags: List[str]
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None


class NoteList(BaseModel):
    """Response model for multiple notes"""
    notes: List[NoteResponse]
    total: int