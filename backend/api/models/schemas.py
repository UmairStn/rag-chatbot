"""
Request and Response models for FastAPI endpoints
"""
from pydantic import BaseModel
from typing import Optional, Union, List

class IngestRequest(BaseModel):
    """Request model for website ingestion endpoint"""
    url: Union[str, List[str]]  # Accept single URL or list of URLs
    client_id: str
    use_sitemap: Optional[bool] = False
    api_provider: Optional[str] = "google"  # 'google' (default) or 'openrouter' - for backend indexing only
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.example.com",
                "client_id": "shop_001",
                "use_sitemap": True
            },
            "examples": [
                {
                    "summary": "Scrape using sitemap with Google API",
                    "value": {
                        "url": "https://www.example.com",
                        "client_id": "shop_001",
                        "use_sitemap": True,
                        "api_provider": "google"
                    }
                },
                {
                    "summary": "Scrape using OpenRouter API",
                    "value": {
                        "url": "https://www.example.com",
                        "client_id": "shop_001",
                        "use_sitemap": False,
                        "api_provider": "openrouter"
                    }
                }
            ]
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
