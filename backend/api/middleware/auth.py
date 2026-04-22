"""
Authentication middleware for API key validation
"""
from fastapi import HTTPException, status
from fastapi.security import APIKeyHeader
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

class APIKeyValidator:
    """Validates API keys for protecting endpoints"""
    
    @staticmethod
    def get_valid_api_key() -> str:
        """Get the valid API key from environment"""
        api_key = os.getenv("API_KEY")
        if not api_key:
            raise ValueError("API_KEY not set in environment variables")
        return api_key
    
    @staticmethod
    async def verify_api_key(api_key: str) -> str:
        """
        Verify the provided API key matches the configured key
        
        Args:
            api_key: The API key from request header
            
        Returns:
            The verified API key
            
        Raises:
            HTTPException: If API key is invalid
        """
        try:
            valid_key = APIKeyValidator.get_valid_api_key()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API configuration error"
            )
        
        if api_key != valid_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        return api_key
