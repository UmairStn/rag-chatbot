"""
Website ingestion endpoint - POST /ingest
Handles URL submission and triggers vectorization
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from api.models.schemas import IngestRequest, IngestResponse, ErrorResponse
from api.middleware.auth import APIKeyValidator, API_KEY_HEADER
from services.indexer import index_website_data

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

@router.post(
    "",
    response_model=IngestResponse,
    summary="Ingest a website",
    description="Submit a URL to be scraped, chunked, and vectorized for RAG"
)
async def ingest_website(
    request: IngestRequest,
    api_key: str = Depends(API_KEY_HEADER)
):
    """
    Ingest website(s) for the RAG system
    
    **Parameters:**
    - **url**: Website URL(s) to ingest. Can be:
      - Single URL string: `"https://example.com"`
      - Multiple URLs array: `["https://example.com/home", "https://example.com/shop"]`
    - **client_id**: Unique identifier for the client/shop
    - **use_sitemap**: If true, scrapes entire website using sitemap.xml (default: false)
    - **api_provider**: Backend API for embeddings - 'google' (default) or 'openrouter' (manual control only)
    
    **Headers:**
    - **X-API-Key**: Your API key for authentication
    
    **Returns:**
    - **status**: "success" if ingestion completed
    - **message**: Description of the operation
    - **chunks_indexed**: Number of chunks created
    - **client_id**: The client ID used
    
    **Examples:**
    
    Scrape single URL with Google:
    ```json
    {
        "url": "https://example.com",
        "client_id": "shop_001",
        "api_provider": "google"
    }
    ```
    
    Scrape entire website using OpenRouter:
    ```json
    {
        "url": "https://example.com",
        "client_id": "shop_001",
        "use_sitemap": true,
        "api_provider": "openrouter"
    }
    ```
    """
    try:
        # Verify API key
        await APIKeyValidator.verify_api_key(api_key)
        
        # Validate inputs
        if not request.url or not request.client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="url and client_id are required"
            )
        
        # If url is a list, validate it's not empty
        if isinstance(request.url, list) and len(request.url) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="url list cannot be empty"
            )
        
        # Index the website
        result = index_website_data(
            request.url, 
            request.client_id, 
            use_sitemap=request.use_sitemap, 
            api_provider=request.api_provider,
            force_reindex=request.force_reindex
        )
        
        # Handle already indexed response
        if isinstance(result, dict) and result.get("status") == "already_indexed":
            return IngestResponse(
                status="already_indexed",
                message="Data already indexed for this client",
                client_id=request.client_id
            )
        
        # Handle success response
        chunks_indexed = result.get("chunks_indexed") if isinstance(result, dict) else result
        
        return IngestResponse(
            status="success",
            message=f"Successfully indexed website for {request.client_id}",
            chunks_indexed=chunks_indexed,
            client_id=request.client_id
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Ingest error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}"
        )