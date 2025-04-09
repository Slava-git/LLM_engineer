from .vectorstore import DenseVectorSearch
from .tag_vectorstore import TagVectorStore
from ..storage import storage
from ..config import logger

vector_search = DenseVectorSearch()

tag_vector_store = TagVectorStore(storage=storage)