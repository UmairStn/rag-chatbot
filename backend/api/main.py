"""
Main FastAPI application
FastAPI web service for RAG chatbot with website ingestion
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import routes
from api.routes import ingest, chat

# Create FastAPI app with simple configuration
app = FastAPI(
    title="RAG Chatbot API",
    description="Ingest websites and chat with AI using Retrieval Augmented Generation (RAG)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS middleware
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(ingest.router)
app.include_router(chat.router)

# Health check endpoint
@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Check if the API is running"
)
async def health_check():
    """Check API health status"""
    return {
        "status": "healthy",
        "service": "RAG Chatbot API",
        "version": "1.0.0"
    }

# Root endpoint
@app.get(
    "/",
    tags=["System"],
    summary="API Information",
    description="Get API information"
)
async def root():
    """Welcome endpoint with API information"""
    return {
        "service": "RAG Chatbot API",
        "version": "1.0.0",
        "message": "Welcome to the RAG Chatbot API",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "ingest": "/ingest",
            "chat": "/chat"
        }
    }

# Custom OpenAPI schema to include API key in security
def custom_openapi():
    """Add API key requirement to OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="RAG Chatbot API",
        version="1.0.0",
        description="Ingest websites and chat with AI using Retrieval Augmented Generation",
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API Key for authentication"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": "HTTP Exception",
            "message": exc.detail,
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error": "Internal Server Error",
            "message": str(exc),
        },
    )

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    reload = os.getenv("API_RELOAD", "True").lower() == "true"
    
    # Run the server
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
