#!/usr/bin/env python3
"""
Test script to verify lesson expansion works
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.course_storage import CourseStorage
from services.course_service import expand_lesson_plan

def test_lesson_expansion():
    """Test the lesson expansion system"""
    print("🧪 Testing Lesson Expansion System")
    print("=" * 40)
    
    # Initialize storage
    course_storage = CourseStorage()
    
    # Test getting lesson agenda
    print("🔍 Testing lesson agenda retrieval...")
    agenda = course_storage.get_lesson_agenda("learn_C", 1, 1, 1)
    print(f"✅ Agenda: {agenda}")
    
    # Test getting detailed lesson plan
    print("\n🔍 Testing detailed lesson plan retrieval...")
    detailed_plan = course_storage.get_detailed_lesson_plan("learn_C", 1, 1, 1)
    print(f"✅ Detailed plan exists: {detailed_plan is not None}")
    if detailed_plan:
        print(f"📝 Plan preview: {detailed_plan[:200]}...")
    
    # Test lesson expansion
    print("\n🚀 Testing lesson expansion...")
    try:
        expanded_plan = expand_lesson_plan("learn_C", 1, 1, 1)
        if expanded_plan and not expanded_plan.startswith("Error"):
            print("✅ Lesson expansion successful!")
            print(f"📝 Expanded plan length: {len(expanded_plan)}")
            print(f"📝 Plan preview: {expanded_plan[:300]}...")
        else:
            print(f"❌ Lesson expansion failed: {expanded_plan}")
    except Exception as e:
        print(f"❌ Lesson expansion error: {e}")
    
    print("\n🎯 Test completed!")

if __name__ == "__main__":
    test_lesson_expansion()
