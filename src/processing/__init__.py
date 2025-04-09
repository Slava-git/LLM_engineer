from .extractor import StructureExtractor
from .rag import RAGPipeline
from .pipeline import NoteProcessor
from ..storage import storage
from ..search import vector_search, tag_vector_store
from ..config import logger, OPENAI_API_KEY

if OPENAI_API_KEY:
    rag_pipeline = RAGPipeline(vector_search)
    logger.info("Initialized RAG pipeline")
else:
    rag_pipeline = None
    logger.warning("OpenAI API key not set. RAG pipeline disabled.")

note_processor = NoteProcessor(
    storage=storage,
    vector_search=vector_search,
    tag_vector_store=tag_vector_store
)