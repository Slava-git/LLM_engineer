from typing import Dict, List, Any, Optional
import uuid
import datetime
from haystack import Pipeline
from ..models.note import Note
from ..storage.base import BaseStorage
from ..search.vectorstore import DenseVectorSearch
from ..search.tag_vectorstore import TagVectorStore
from .extractor import StructureExtractor
from ..config import logger, OPENAI_API_KEY


class NoteProcessor:
    """
    Process notes with structured data extraction, tagging, and storage.
    """
    
    def __init__(self, storage: BaseStorage, vector_search: DenseVectorSearch, tag_vector_store: TagVectorStore):
        """
        Initialize the NoteProcessor.
        
        Args:
            storage: Storage backend
            vector_search: Vector search component
            tag_vector_store: Tag vector store component
        """
        self.storage = storage
        self.vector_search = vector_search
        self.tag_vector_store = tag_vector_store
        
        if OPENAI_API_KEY:
            self.extractor = StructureExtractor()
            
            self.extraction_pipeline = Pipeline()
            self.extraction_pipeline.add_component("extractor", self.extractor)
            logger.info("Initialized structure extraction pipeline")
        else:
            self.extractor = None
            self.extraction_pipeline = None
            logger.warning("OpenAI API key not set. Structure extraction disabled.")
    
    async def process_note(self, note_content: str, tags: Optional[List[str]] = None, note_id: Optional[str] = None) -> Note:
        """
        Process a note - extract structured data, generate tags, and save to storage.
        
        Args:
            note_content: The content of the note
            tags: Optional list of initial tags
            note_id: Optional ID for the note (generated if not provided)
            
        Returns:
            The processed note
        """
        processed_tags = []
        metadata = {}
        
        if self.extraction_pipeline:
            try:
                result = self.extraction_pipeline.run({"extractor": {"text": note_content}})
                
                structured_data = result["extractor"]["structured_data"]
                structure_type = result["extractor"]["structure_type"]
                suggested_tags = result["extractor"]["suggested_tags"]
                confidence = result["extractor"]["confidence"]
                
                metadata = {
                    "structured_data": structured_data,
                    "structure_type": structure_type,
                    "confidence": confidence
                }
                
                structure_tag_result = self.tag_vector_store.run(tag=structure_type)
                processed_tags.append(structure_tag_result["processed_tag"])
                
                for tag in suggested_tags:
                    if tag: 
                        tag_result = self.tag_vector_store.run(tag=tag)
                        processed_tag = tag_result["processed_tag"]
                        if processed_tag and processed_tag not in processed_tags:
                            processed_tags.append(processed_tag)
            except Exception as e:
                logger.error(f"Error in structure extraction: {str(e)}")
        
        if tags:
            for tag in tags:
                if tag:
                    tag_result = self.tag_vector_store.run(tag=tag)
                    processed_tag = tag_result["processed_tag"]
                    if processed_tag and processed_tag not in processed_tags:
                        processed_tags.append(processed_tag)
        
        note = Note(
            id=note_id or str(uuid.uuid4()),
            content=note_content,
            tags=processed_tags,
            metadata=metadata,
            created_at=datetime.datetime.now().isoformat(),
            updated_at=datetime.datetime.now().isoformat()
        )
        
        self.storage.save_note(note)
        
        self.vector_search.index_notes(note)
        
        return note
    
    async def update_note(self, note_id: str, content: Optional[str] = None, tags: Optional[List[str]] = None) -> Optional[Note]:
        """
        Update an existing note.
        
        Args:
            note_id: The note ID
            content: New content (None to keep existing)
            tags: New tags (None to keep existing)
            
        Returns:
            The updated note or None if not found
        """
        note = self.storage.get_note(note_id)
        
        if not note:
            return None
        
        if content is not None:
            note.content = content
            
            if self.extraction_pipeline:
                try:
                    result = self.extraction_pipeline.run({"extractor": {"text": content}})
                    
                    note.metadata = {
                        "structured_data": result["extractor"]["structured_data"],
                        "structure_type": result["extractor"]["structure_type"],
                        "confidence": result["extractor"]["confidence"]
                    }
                except Exception as e:
                    logger.error(f"Error re-extracting metadata: {str(e)}")
            
        if tags is not None:
            processed_tags = []
            
            for tag in tags:
                if tag:  # Skip empty tags
                    tag_result = self.tag_vector_store.run(tag=tag)
                    processed_tag = tag_result["processed_tag"]
                    if processed_tag and processed_tag not in processed_tags:
                        processed_tags.append(processed_tag)
            
            note.tags = processed_tags
        
        note.updated_at = datetime.datetime.now().isoformat()
        
        self.storage.save_note(note)
        
        self.vector_search.delete_from_index(note_id)
        self.vector_search.index_notes(note)
        
        return note