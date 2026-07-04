#!/usr/bin/env python
"""
Diagnostic script to check available Google Generative AI models
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.core.config import Config

try:
    import google.generativeai as genai
    
    # Set API key
    genai.configure(api_key=Config.GOOGLE_API_KEY)
    
    # List available models
    print("=" * 60)
    print("📋 Available Google Generative AI Models:")
    print("=" * 60)
    
    models = genai.list_models()
    embedding_models = []
    chat_models = []
    
    for model in models:
        model_name = model.name
        print(f"\n📦 {model_name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description}")
        
        # Categorize
        if 'embedding' in model_name.lower():
            embedding_models.append(model_name)
        if 'gemini' in model_name.lower():
            chat_models.append(model_name)
    
    print("\n" + "=" * 60)
    print("✅ EMBEDDING MODELS:")
    if embedding_models:
        for m in embedding_models:
            print(f"  - {m}")
    else:
        print("  ❌ No embedding models found")
    
    print("\n✅ CHAT MODELS:")
    if chat_models:
        for m in chat_models:
            print(f"  - {m}")
    else:
        print("  ❌ No chat models found")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Troubleshooting:")
    print("  1. Check if GOOGLE_API_KEY is set correctly in .env")
    print("  2. Verify API key has access to Google Generative AI")
    print("  3. Check if Generative AI API is enabled in Google Cloud")
