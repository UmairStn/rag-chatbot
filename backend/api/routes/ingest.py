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
    Ingest a website for the RAG system
    
    **Parameters:**
    - **url**: Website URL to ingest (e.g., https://example.com)
    - **client_id**: Unique identifier for the client/shop
    
    **Headers:**
    - **X-API-Key**: Your API key for authentication
    
    **Returns:**
    - **status**: "success" if ingestion completed
    - **message**: Description of the operation
    - **chunks_indexed**: Number of chunks created
    - **client_id**: The client ID used
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
        
        # Index the website
        result = index_website_data(request.url, request.client_id)
        
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
        logger = logging.getLogger(__name__)
        logger.error(f"Ingest error: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Indexing failed. Please contact support."
        )