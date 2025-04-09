from typing import List, Union, Optional
import logging
from haystack import Pipeline
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.embedders import SentenceTransformersTextEmbedder, SentenceTransformersDocumentEmbedder
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from ..models.note import Note
from ..config import logger, USE_IN_MEMORY_QDRANT, QDRANT_HOST, QDRANT_PORT

class DenseVectorSearch:
    """Manages dense vector search with Haystack 2.x"""
    
    def __init__(self):
        """Initialize the dense vector search"""
        if USE_IN_MEMORY_QDRANT:
            self.document_store = QdrantDocumentStore(
                ":memory:",
                recreate_index=True,
                return_embedding=True,
                embedding_dim=1024
            )
            logger.info("Initialized in-memory QdrantDocumentStore")
        else:
            self.document_store = QdrantDocumentStore(
                host=QDRANT_HOST,
                port=QDRANT_PORT,
                recreate_index=False,
                return_embedding=True,
                embedding_dim=1024
            )
            logger.info(f"Initialized Qdrant connection to {QDRANT_HOST}:{QDRANT_PORT}")
        
        self.doc_embedder = SentenceTransformersDocumentEmbedder(
            model="intfloat/multilingual-e5-large", 
            meta_fields_to_embed=["tags"]
        )
        self.text_embedder = SentenceTransformersTextEmbedder(
            model="intfloat/multilingual-e5-large",
            prefix="Represent this sentence for searching relevant passages: "
        )
        
        logger.info("Warming up document embedder...")
        self.doc_embedder.warm_up()
        logger.info("Warming up text embedder...")
        self.text_embedder.warm_up()
        
        logger.info("Initialized and warmed up embedders")
        
        self.retriever = QdrantEmbeddingRetriever(
            document_store=self.document_store,
            top_k=10
        )
        
        logger.info("Initialized retriever")
        
        self.cleaner = DocumentCleaner()
        
        self.splitter = DocumentSplitter(
            split_by="word", 
            split_length=1000,
            split_overlap=50
        )
        
        self.query_pipeline = Pipeline()
        self.query_pipeline.add_component("text_embedder", self.text_embedder)
        self.query_pipeline.add_component("retriever", self.retriever)
        
        self.query_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        
        logger.info("Initialized query pipeline")
    
    def index_notes(self, notes: Union[Note, List[Note]]):
        """Index notes for vector search"""
        if isinstance(notes, Note):
            notes = [notes]
        
        documents = [note.to_haystack_document() for note in notes]
        logger.info(f"Converting {len(documents)} notes to documents")
        
        cleaned_docs = self.cleaner.run(documents=documents)["documents"]
        logger.info(f"Cleaned {len(cleaned_docs)} documents")
        
        processed_docs = cleaned_docs
        
        try:
            logger.info(f"Embedding {len(processed_docs)} documents")
            if processed_docs:
                logger.info(f"Example document: {processed_docs[0].content[:100]}...")
                
            embedded_docs = self.doc_embedder.run(documents=processed_docs)["documents"]
            logger.info(f"Successfully embedded {len(embedded_docs)} documents")
            
            if embedded_docs and hasattr(embedded_docs[0], 'embedding') and embedded_docs[0].embedding is not None:
                embedding = embedded_docs[0].embedding
                logger.info(f"Example embedding type: {type(embedding)}, shape or length: {len(embedding) if isinstance(embedding, list) else 'unknown'}")
            else:
                logger.warning("No embeddings found in documents")
            
            logger.info("Writing documents to document store")
            self.document_store.write_documents(embedded_docs)
            logger.info(f"Successfully indexed {len(embedded_docs)} documents")
            
        except Exception as e:
            logger.error(f"Error embedding documents: {str(e)}", exc_info=True)
            raise
    
    def delete_from_index(self, note_id: str):
        """Remove a note from the index (including any splits)"""
        try:
            self.document_store.delete_documents(ids=[note_id])
            logger.info(f"Deleted document with ID {note_id} from index")
        except Exception as e:
            logger.error(f"Error deleting document from index: {str(e)}", exc_info=True)
    
    def search(self, query: str, top_k: int = 5) -> List[Note]:
        """Search for notes using dense vector similarity"""
        logger.info(f"Searching for: '{query}' with top_k={top_k}")
        
        try:
            doc_count = self.document_store.count_documents()
            logger.info(f"Document store contains {doc_count} documents")
            
            if doc_count == 0:
                logger.warning("No documents in the document store")
                return []

            results = self.query_pipeline.run(
                {"text_embedder": {"text": query},
                 "retriever": {"top_k": top_k}}
            )
            
            documents = results["retriever"]["documents"]
            logger.info(f"Search returned {len(documents)} documents")
            
            for i, doc in enumerate(documents):
                logger.info(f"Result {i+1}: ID={doc.id}, Score={doc.score if hasattr(doc, 'score') else 'N/A'}, Content={doc.content[:50]}...")
            
            notes = [Note.from_haystack_document(doc) for doc in documents]
            return notes
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}", exc_info=True)
            return []