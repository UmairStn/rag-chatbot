import logging

"""
Chat endpoint - POST /chat
Handles user queries against indexed knowledge base
"""
from fastapi import APIRouter, Depends, HTTPException, status
from api.models.schemas import ChatRequest, ChatResponse, ErrorResponse
from api.middleware.auth import APIKeyValidator, API_KEY_HEADER
from services.chatbot import get_chatbot_response

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post(
    "",
    response_model=ChatResponse,
    summary="Chat with RAG bot",
    description="Submit a query to get an AI-powered answer based on indexed website content"
)
async def chat(
    request: ChatRequest,
    api_key: str = Depends(API_KEY_HEADER)
):
    """
    Chat with the RAG-powered chatbot
    
    **Parameters:**
    - **query**: User question/message
    - **client_id**: Unique identifier for the client/shop
    
    **Headers:**
    - **X-API-Key**: Your API key for authentication
    
    **Returns:**
    - **status**: "success" if query was answered
    - **answer**: AI-generated response based on indexed content
    - **client_id**: The client ID used
    
    **Note:**
    - The website must be indexed first using the /ingest endpoint before queries will work
    - API provider is controlled in backend code only (not via request)
    - To switch APIs: Edit CHAT_API_PROVIDER in services/chatbot.py
    """
    try:
        # Verify API key
        await APIKeyValidator.verify_api_key(api_key)
        
        # Validate inputs
        if not request.query or not request.client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="query and client_id are required"
            )
        
        # Get response from chatbot service
        answer = get_chatbot_response(request.query, request.client_id)
        
        return ChatResponse(
            status="success",
            answer=answer,
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
        logger.error(f"Chat API Error: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sorry, I'm temporarily unavailable. Please try again in a moment."
        )