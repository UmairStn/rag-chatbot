"""
Request and Response models for FastAPI endpoints
"""
from pydantic import BaseModel
from typing import Optional

class IngestRequest(BaseModel):
    """Request model for website ingestion endpoint"""
    url: str
    client_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.example.com",
                "client_id": "shop_001"
            }
        }

class IngestResponse(BaseModel):
    """Response model for website ingestion"""
    status: str
    message: str
    chunks_indexed: Optional[int] = None
    client_id: str

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    query: str
    client_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What products do you offer?",
                "client_id": "shop_001"
            }
        }

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    status: str
    answer: str
    client_id: str

class ErrorResponse(BaseModel):
    """Generic error response"""
    status: str
    error: str
    message: str
