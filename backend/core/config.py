import os
from dotenv import load_dotenv
from pathlib import Path

# Load variables from the .env file
load_dotenv()

class Config:
    # Use the standard LangChain variable name for Google Gemini
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Path where the Vector Database will save its files on your disk
    VECTOR_DB_PATH = str(Path(__file__).parent.parent / "data" / "vector_db")

    @staticmethod
    def validate():
        if not Config.GOOGLE_API_KEY:
            raise ValueError("❌ GOOGLE_API_KEY missing! Add it to your .env file.")