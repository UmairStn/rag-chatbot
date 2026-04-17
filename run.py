#!/usr/bin/env python
"""
Simple runner script for the RAG chatbot
Run with: python run.py
"""
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from backend.main import main

if __name__ == "__main__":
    main()
