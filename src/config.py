import os
from typing import Any, Dict, Optional

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "smart_notes")

USE_IN_MEMORY_QDRANT = os.getenv("USE_IN_MEMORY_QDRANT", "true").lower() == "true"
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

STORAGE_TYPE = os.getenv("STORAGE_TYPE", "memory")

class AppConfig:
    """Application configuration"""
    
    def __init__(self):
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.title = "Smart Notes API"
        self.version = "0.1.0"
        self.description = "API for smart notes with vector search and tagging"
        self.openapi_url = "/openapi.json"
        self.docs_url = "/docs"
        
    def dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

app_config = AppConfig()


import logging

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("smart_notes")