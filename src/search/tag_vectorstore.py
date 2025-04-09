from typing import List, Optional, Dict, Any
from haystack import Pipeline, component
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack.dataclasses import Document
from ..storage.base import BaseStorage
from ..config import logger, USE_IN_MEMORY_QDRANT, QDRANT_HOST, QDRANT_PORT

@component
class TagVectorStore:
    """
    A component to manage a vector database of tags for similarity matching.
    """
    
    def __init__(self, storage: BaseStorage, similarity_threshold: float = 0.95):
        """
        Initialize the tag vector store.
        
        Args:
            storage: Storage for persistence
            similarity_threshold: Threshold for considering tags similar (0-1)
        """
        self.storage = storage

        if USE_IN_MEMORY_QDRANT:
            self.document_store = QdrantDocumentStore(
                ":memory:",
                embedding_dim=384,
                recreate_index=True,
                return_embedding=True
            )
        else:
            self.document_store = QdrantDocumentStore(
                host=QDRANT_HOST,
                port=QDRANT_PORT,
                embedding_dim=384,
                recreate_index=False,
                return_embedding=True
            )
        
        self.embedder = SentenceTransformersTextEmbedder(model="intfloat/multilingual-e5-small")
        
        self.embedder.warm_up()
        
        self.retriever = QdrantEmbeddingRetriever(
            document_store=self.document_store,
            top_k=3
        )
        
        self.retrieval_pipeline = Pipeline()
        self.retrieval_pipeline.add_component("embedder", self.embedder)
        self.retrieval_pipeline.add_component("retriever", self.retriever)
        self.retrieval_pipeline.connect("embedder.embedding", "retriever.query_embedding")
        
        self.similarity_threshold = similarity_threshold
        
        self._initialize_from_storage()
    
    def _initialize_from_storage(self):
        """
        Initialize the vector store with existing tags from storage
        """
        existing_tags = self.storage.get_all_tags()
        
        qdrant_count = self.document_store.count_documents()
        
        if qdrant_count < len(existing_tags):
            logger.info(f"Adding {len(existing_tags)} existing tags from storage to Qdrant")
            
            for tag in existing_tags:
                try:
                    if not self._tag_exists_in_qdrant(tag):
                        self._add_tag_to_qdrant(tag)
                except Exception as e:
                    logger.error(f"Error adding tag '{tag}' to Qdrant: {str(e)}")
    
    def _tag_exists_in_qdrant(self, tag: str) -> bool:
        """
        Check if a tag exists in Qdrant
        
        Args:
            tag: The tag to check
            
        Returns:
            True if the tag exists, False otherwise
        """
        try:
            docs = self.document_store.get_documents_by_id([tag])
            return len(docs) > 0
        except:
            return False
    
    def _add_tag_to_qdrant(self, tag: str) -> None:
        """
        Add a tag to Qdrant without checking for duplicates
        
        Args:
            tag: The tag to add
        """
        doc = Document(content=tag, id=tag)
        
        embedded_result = self.embedder.run(text=tag)
        doc.embedding = embedded_result["embedding"]
        
        self.document_store.write_documents([doc])
    
    @component.output_types(processed_tag=str, is_new=bool)
    def run(self, tag: str):
        """
        Process a tag through the vector store - find similar or create new.
        
        Args:
            tag: The tag to process
            
        Returns:
            The processed tag (either existing similar tag or new normalized tag)
            and whether it's a new tag
        """
        original_tag = tag
        is_new = False
        
        processed_tag, is_new = self.get_or_create_tag(tag)
        return {"processed_tag": processed_tag, "is_new": is_new}
    
    def add_tag(self, tag: str) -> None:
        """
        Add a new tag to both vector store and storage
        
        Args:
            tag: The tag to add
        """
        self._add_tag_to_qdrant(tag)
        
        self.storage.save_tag(tag)
        
        logger.info(f"Added tag to stores: {tag}")
    
    def find_similar_tag(self, tag: str) -> Optional[str]:
        """
        Find a similar existing tag or return None if no close match found.
        
        Args:
            tag: The tag to check for similarity
            
        Returns:
            Similar existing tag or None
        """
        if self.document_store.count_documents() == 0:
            return None
            
        try:
            results = self.retrieval_pipeline.run(
                {"embedder": {"text": tag},
                 "retriever": {"top_k": 1}}
            )
            
            documents = results["retriever"]["documents"]
            
            if documents and len(documents) > 0 and hasattr(documents[0], 'score') and documents[0].score >= self.similarity_threshold:
                similar_tag = documents[0].content
                logger.info(f"Found similar tag: '{tag}' → '{similar_tag}' (score: {documents[0].score:.2f})")
                return similar_tag
        except Exception as e:
            logger.error(f"Error finding similar tag for '{tag}': {str(e)}")
        
        return None
    
    def get_or_create_tag(self, tag: str) -> tuple[str, bool]:
        """
        Get a similar existing tag or create a new one.
        
        Args:
            tag: The tag to process
            
        Returns:
            The existing similar tag or the new tag, and whether it's new
        """
        normalized_tag = self._normalize_tag(tag)
        
        similar_tag = self.find_similar_tag(normalized_tag)
        
        if similar_tag:
            return similar_tag, False
        
        self.add_tag(normalized_tag)
        return normalized_tag, True
    
    def _normalize_tag(self, tag: str) -> str:
        """
        Normalize a tag for consistency.
        
        Args:
            tag: The tag to normalize
            
        Returns:
            Normalized tag
        """
        tag = tag.lower()
        
        tag = ''.join(c for c in tag if c.isalnum() or c == ':' or c == '_')
        
        return tag