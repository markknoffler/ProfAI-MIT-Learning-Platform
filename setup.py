#!/usr/bin/env python3
"""
Setup script for ProfAI MIT Learning Platform
This script helps users configure their environment variables.
"""

import os
import sys

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return
    
    if os.path.exists('env.example'):
        with open('env.example', 'r') as f:
            content = f.read()
        
        with open('.env', 'w') as f:
            f.write(content)
        
        print("✅ Created .env file from template")
        print("📝 Please edit .env file with your actual API keys")
    else:
        print("❌ env.example not found")

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import streamlit
        import chromadb
        import requests
        print("✅ All required dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")

def main():
    print("🚀 ProfAI MIT Setup")
    print("=" * 50)
    
    create_env_file()
    check_dependencies()
    
    print("\n📋 Next Steps:")
    print("1. Edit .env file with your API keys")
    print("2. Set up Ollama server with ngrok")
    print("3. Run: streamlit run app.py")
    
    print("\n🔑 Required API Keys:")
    print("- ElevenLabs API key (for voice features)")
    print("- YouTube Data API key (for video integration)")
    print("- ngrok endpoint (for Ollama server)")

if __name__ == "__main__":
    main()
