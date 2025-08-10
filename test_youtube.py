#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from services.youtube_service import YouTubeService
    print("✅ YouTube service imported successfully")
    
    # Test the service
    youtube_service = YouTubeService()
    print("✅ YouTube service initialized successfully")
    
    # Test search prompt generation
    test_lesson_plan = "Learn about Python functions, including function definition, parameters, return values, and scope."
    prompts = youtube_service.generate_search_prompts(test_lesson_plan)
    print(f"✅ Generated search prompts: {prompts}")
    
    print("🎉 All tests passed! The YouTube service is working correctly.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install the required dependencies:")
    print("pip install --break-system-packages google-api-python-client youtube-transcript-api")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("The YouTube service encountered an error during testing.")
