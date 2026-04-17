#!/usr/bin/env python3
"""Simple script to test API key and find available embedding models."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.core.config import Config

try:
    import google.generativeai as genai
    
    print("✅ google.generativeai imported successfully")
    
    # Configure with API key
    genai.configure(api_key=Config.GOOGLE_API_KEY)
    print(f"✅ API configured with key: {Config.GOOGLE_API_KEY[:20]}...")
    
    # Try to list models
    print("\n📋 Fetching available models...")
    models = genai.list_models()
    
    print("\n" + "="*60)
    print("AVAILABLE EMBEDDING MODELS:")
    print("="*60)
    embedding_models = [m for m in models if 'embedding' in m.name.lower()]
    if embedding_models:
        for model in embedding_models:
            print(f"  • {model.name}")
            # Try to extract supported methods
            if hasattr(model, 'supported_generation_methods'):
                print(f"    Methods: {model.supported_generation_methods}")
    else:
        print("  ⚠️  No embedding models found!")
        print("\n  Available models:")
        for model in models:
            print(f"    • {model.name}")
    
    print("\n" + "="*60)
    print("AVAILABLE CHAT MODELS:")
    print("="*60)
    chat_models = [m for m in models if 'generateContent' in str(getattr(m, 'supported_generation_methods', []))]
    if chat_models:
        for model in chat_models[:5]:  # Show first 5
            print(f"  • {model.name}")
    else:
        print("  ⚠️  No chat models found!")
    
except ModuleNotFoundError as e:
    print(f"❌ Error: {e}")
    print("\n💡 Troubleshooting:")
    print("  The google-generativeai package is still installing.")
    print("  Please wait a moment and try again.")
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Troubleshooting:")
    print("  1. Check if GOOGLE_API_KEY is set correctly in .env")
    print("  2. Verify API key has access to Google Generative AI")
    print("  3. Check if Generative AI API is enabled in Google Cloud")
    print(f"  4. Full error: {type(e).__name__}: {e}")
