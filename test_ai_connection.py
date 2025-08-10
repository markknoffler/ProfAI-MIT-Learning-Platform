#!/usr/bin/env python3
"""
Test script to verify AI connection and debug the course generation issue
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.ollama_client import call_model, _is_configured
from services.course_service import _test_ai_connection, generate_course_structure

def main():
    print("🔍 Testing AI Connection Components")
    print("=" * 50)
    
    # Test 1: Check configuration
    print("\n1. Configuration Check:")
    print(f"   OLLAMA_URL configured: {_is_configured()}")
    
    # Test 2: Test basic AI call
    print("\n2. Basic AI Call Test:")
    try:
        response = call_model([
            {"role": "system", "content": "You are a test bot. Respond with exactly: 'Hello World'"},
            {"role": "user", "content": "Say hello"}
        ])
        print(f"   ✅ AI Response: {response[:100]}...")
    except Exception as e:
        print(f"   ❌ AI Call Failed: {str(e)}")
    
    # Test 3: Test AI connection test
    print("\n3. AI Connection Test:")
    try:
        success = _test_ai_connection()
        print(f"   {'✅' if success else '❌'} Connection Test: {'Success' if success else 'Failed'}")
    except Exception as e:
        print(f"   ❌ Connection Test Error: {str(e)}")
    
    # Test 4: Test course generation
    print("\n4. Course Generation Test:")
    try:
        course = generate_course_structure("test-user", "Python Basics")
        if "sections" in course and len(course["sections"]) > 0:
            print(f"   ✅ Course Generated: {len(course['sections'])} sections")
            print(f"   📚 First section: {course['sections'][0]['name']}")
        else:
            print(f"   ❌ Course Generation Failed: Invalid structure")
            print(f"   📄 Course data: {course}")
    except Exception as e:
        print(f"   ❌ Course Generation Error: {str(e)}")

if __name__ == "__main__":
    main()
