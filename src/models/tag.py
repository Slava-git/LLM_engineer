from pydantic import BaseModel
from typing import Dict, List, Optional, Any

class Tag(BaseModel):
    """Tag data model"""
    name: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "appointment",
                "created_at": "2024-04-08T10:00:00.000Z",
                "updated_at": "2024-04-08T10:00:00.000Z"
            }
        }


class TagList(BaseModel):
    """Response model for multiple tags"""
    tags: List[Tag]
    total: int


class TagProcessRequest(BaseModel):
    """Request model for processing a tag"""
    tag: str


class TagProcessResponse(BaseModel):
    """Response model for processed tag"""
    original_tag: str
    processed_tag: str
    is_new: bool