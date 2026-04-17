# CLI script to test Phase 1
import sys
from pathlib import Path

# Add parent directory to path so imports work when running from backend/
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.config import Config
from backend.services.indexer import index_website_data
from backend.services.chatbot import get_chatbot_response

def main():
    # Verify API key exists
    Config.validate()
    
    # Define a sample client and website
    client = "shop_001"
    WEBSITE_URL = "https://www.simplytek.lk/" # Replace with a real website to test!
    
    # STEP 1: Learn the website
    index_website_data(WEBSITE_URL, client)
    
    # STEP 2: Start a chat loop
    print("\n--- RAG CHATBOT ACTIVE ---")
    while True:
        query = input("\nYou: ")
        if query.lower() in ["exit", "quit"]: break
        
        answer = get_chatbot_response(query, client)
        print(f"Bot: {answer}")

if __name__ == "__main__":
    main()