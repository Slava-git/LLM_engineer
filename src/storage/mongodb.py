from typing import Dict, List, Optional, Any
import datetime
from pymongo import MongoClient
from .base import BaseStorage
from ..models.note import Note
from ..config import MONGODB_URI, DB_NAME, logger

class MongoDBStorage(BaseStorage):
    """Storage for notes and tags using MongoDB"""
    
    def __init__(self, uri: str = MONGODB_URI, db_name: str = DB_NAME):
        """
        Initialize MongoDB storage
        
        Args:
            uri: MongoDB connection URI
            db_name: Database name
        """
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.notes_collection = self.db["notes"]
        self.tags_collection = self.db["tags"]
        
        self.notes_collection.create_index("id", unique=True)
        self.tags_collection.create_index("name", unique=True)
        
        logger.info(f"Connected to MongoDB: {db_name}")
    
    def save_note(self, note: Note) -> Note:
        """Save a note to MongoDB"""
        note_dict = note.to_dict()
        
        if "created_at" not in note_dict:
            note_dict["created_at"] = datetime.datetime.now().isoformat()
        
        note_dict["updated_at"] = datetime.datetime.now().isoformat()
        
        self.notes_collection.update_one(
            {"id": note_dict["id"]},
            {"$set": note_dict},
            upsert=True
        )
        
        for tag in note.tags:
            self.save_tag(tag)
        
        return note
    
    def get_note(self, note_id: str) -> Optional[Note]:
        """Get a note by ID"""
        note_dict = self.notes_collection.find_one({"id": note_id})
        if note_dict:
            note_dict.pop("_id", None)
            return Note.from_dict(note_dict)
        return None
    
    def delete_note(self, note_id: str) -> bool:
        """Delete a note by ID"""
        result = self.notes_collection.delete_one({"id": note_id})
        return result.deleted_count > 0
    
    def get_all_notes(self) -> List[Note]:
        """Get all notes"""
        notes_dict = list(self.notes_collection.find())
        
        notes = []
        for note_dict in notes_dict:
            note_dict.pop("_id", None)
            notes.append(Note.from_dict(note_dict))
            
        return notes
    
    def get_recent_notes(self, limit: int = 10) -> List[Note]:
        """Get recent notes"""
        notes_dict = list(self.notes_collection.find().sort("created_at", -1).limit(limit))
        
        notes = []
        for note_dict in notes_dict:
            note_dict.pop("_id", None)
            notes.append(Note.from_dict(note_dict))
            
        return notes
    
    def search_notes_by_tags(self, tags: List[str]) -> List[Note]:
        """Search notes by tags"""
        notes_dict = list(self.notes_collection.find({"tags": {"$in": tags}}))
        
        notes = []
        for note_dict in notes_dict:
            note_dict.pop("_id", None)
            notes.append(Note.from_dict(note_dict))
            
        return notes
    
    def save_tag(self, tag_name: str) -> None:
        """Save a tag to MongoDB"""
        self.tags_collection.update_one(
            {"name": tag_name},
            {
                "$set": {
                    "name": tag_name,
                    "updated_at": datetime.datetime.now().isoformat()
                },
                "$setOnInsert": {
                    "created_at": datetime.datetime.now().isoformat()
                }
            },
            upsert=True
        )
    
    def get_all_tags(self) -> List[str]:
        """Get all tags"""
        tags = list(self.tags_collection.find({}, {"name": 1}))
        return [tag["name"] for tag in tags]