from typing import Optional
from .base import BaseStorage
from .memory import InMemoryStorage
from .mongodb import MongoDBStorage
from ..config import STORAGE_TYPE, logger

def get_storage() -> BaseStorage:
    """Factory function to get the configured storage implementation"""
    if STORAGE_TYPE.lower() == "mongodb":
        logger.info("Using MongoDB storage")
        return MongoDBStorage()
    else:
        logger.info("Using in-memory storage")
        return InMemoryStorage()

storage = get_storage()