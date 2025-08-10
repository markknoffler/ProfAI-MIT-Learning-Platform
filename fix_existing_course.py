#!/usr/bin/env python3
"""
Script to fix existing courses by adding missing index fields
"""

import json
import os
from pathlib import Path

def fix_existing_course(course_name: str):
    """Fix an existing course by adding index fields"""
    course_dir = Path("courses") / course_name
    course_file = course_dir / "course_structure.json"
    
    if not course_file.exists():
        print(f"❌ Course file not found: {course_file}")
        return False
    
    print(f"🔧 Fixing course: {course_name}")
    
    # Load the course data
    with open(course_file, "r") as f:
        course_data = json.load(f)
    
    # Add index fields
    sections = course_data.get("sections", [])
    print(f"📚 Found {len(sections)} sections")
    
    for section_idx, section in enumerate(sections[:7], 1):
        section["index"] = section_idx
        subsections = section.get("subsections", [])
        print(f"  📖 Section {section_idx}: {section['name']} - {len(subsections)} subsections")
        
        for sub_idx, subsection in enumerate(subsections[:10], 1):
            subsection["index"] = sub_idx
            concepts = subsection.get("concepts", [])
            print(f"    📝 Subsection {sub_idx}: {subsection['name']} - {len(concepts)} concepts")
            
            for concept_idx, concept in enumerate(concepts[:10], 1):
                concept["index"] = concept_idx
    
    # Save the fixed course data
    with open(course_file, "w") as f:
        json.dump(course_data, f, indent=2)
    
    print(f"✅ Course {course_name} fixed successfully!")
    return True

def main():
    """Main function"""
    print("🔧 Course Fixer Script")
    print("=" * 30)
    
    # Fix the existing learn_C course
    if fix_existing_course("learn_C"):
        print("\n🎉 All courses fixed successfully!")
    else:
        print("\n❌ Failed to fix courses")

if __name__ == "__main__":
    main()
