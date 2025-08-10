import os
import json
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

class CourseStorage:
    def __init__(self, base_dir: str = "courses"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def create_course_structure(self, course_name: str, course_data: Dict[str, Any]) -> str:
        """Create the 7x10x10 directory structure for a course"""
        course_dir = self.base_dir / self._safe_name(course_name)
        
        # Remove existing course if it exists
        if course_dir.exists():
            shutil.rmtree(course_dir)
        
        course_dir.mkdir(exist_ok=True)
        
        # Add index fields to the course data for easier navigation
        enhanced_course_data = course_data.copy()
        sections = enhanced_course_data.get("sections", [])
        
        for section_idx, section in enumerate(sections[:7], 1):
            section["index"] = section_idx
            subsections = section.get("subsections", [])
            
            for sub_idx, subsection in enumerate(subsections[:10], 1):
                subsection["index"] = sub_idx
                concepts = subsection.get("concepts", [])
                
                for concept_idx, concept in enumerate(concepts[:10], 1):
                    concept["index"] = concept_idx
        
        # Save the enhanced course data
        with open(course_dir / "course_structure.json", "w") as f:
            json.dump(enhanced_course_data, f, indent=2)
        
        # Create the 7x10x10 directory structure
        for section_idx, section in enumerate(sections[:7], 1):
            section_dir = course_dir / f"module_{section_idx:02d}_{self._safe_name(section['name'])}"
            section_dir.mkdir(exist_ok=True)
            
            # Save section metadata
            with open(section_dir / "section_info.json", "w") as f:
                json.dump({
                    "name": section["name"],
                    "index": section_idx,
                    "created_at": datetime.now().isoformat()
                }, f, indent=2)
            
            subsections = section.get("subsections", [])
            for sub_idx, subsection in enumerate(subsections[:10], 1):
                sub_dir = section_dir / f"submodule_{sub_idx:02d}_{self._safe_name(subsection['name'])}"
                sub_dir.mkdir(exist_ok=True)
                
                # Save subsection metadata
                with open(sub_dir / "subsection_info.json", "w") as f:
                    json.dump({
                        "name": subsection["name"],
                        "index": sub_idx,
                        "section_name": section["name"],
                        "created_at": datetime.now().isoformat()
                    }, f, indent=2)
                
                concepts = subsection.get("concepts", [])
                for concept_idx, concept in enumerate(concepts[:10], 1):
                    concept_dir = sub_dir / f"lesson_{concept_idx:02d}_{self._safe_name(concept['name'])}"
                    concept_dir.mkdir(exist_ok=True)
                    
                    # Save concept metadata and basic agenda
                    with open(concept_dir / "concept_info.json", "w") as f:
                        json.dump({
                            "name": concept["name"],
                            "agenda": concept["agenda"],
                            "index": concept_idx,
                            "subsection_name": subsection["name"],
                            "section_name": section["name"],
                            "created_at": datetime.now().isoformat(),
                            "completed": False,
                            "detailed_plan": None
                        }, f, indent=2)
                    
                    # Create the basic agenda file
                    with open(concept_dir / "agenda.txt", "w") as f:
                        f.write(concept["agenda"])
        
        return str(course_dir)
    
    def get_course_structure(self, course_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve the course structure from storage"""
        course_dir = self.base_dir / self._safe_name(course_name)
        course_file = course_dir / "course_structure.json"
        
        if course_file.exists():
            with open(course_file, "r") as f:
                return json.load(f)
        return None
    
    def get_lesson_agenda(self, course_name: str, module_idx: int, submodule_idx: int, lesson_idx: int) -> Optional[str]:
        """Get the agenda for a specific lesson"""
        course_dir = self.base_dir / self._safe_name(course_name)
        print(f"🔍 Looking for lesson agenda: {course_name} - Module {module_idx}, Submodule {submodule_idx}, Lesson {lesson_idx}")
        print(f"📁 Course directory: {course_dir}")
        
        if not course_dir.exists():
            print(f"❌ Course directory does not exist: {course_dir}")
            return None
        
        # Use a more specific glob pattern to find the exact lesson directory
        lesson_pattern = f"module_{module_idx:02d}_*/submodule_{submodule_idx:02d}_*/lesson_{lesson_idx:02d}_*"
        print(f"🔍 Using pattern: {lesson_pattern}")
        
        # Find the lesson directory
        for lesson_dir in course_dir.glob(lesson_pattern):
            print(f"📁 Found lesson directory: {lesson_dir}")
            if lesson_dir.is_dir():
                agenda_file = lesson_dir / "agenda.txt"
                print(f"📄 Looking for agenda file: {agenda_file}")
                if agenda_file.exists():
                    with open(agenda_file, "r") as f:
                        content = f.read().strip()
                        print(f"✅ Found agenda: {content[:100]}...")
                        return content
                else:
                    print(f"❌ Agenda file does not exist: {agenda_file}")
        
        print("🔄 Pattern matching failed, trying fallback method...")
        
        # Fallback: try to find by looking through the structure systematically
        try:
            for module_dir in course_dir.glob("module_*"):
                if not module_dir.is_dir():
                    continue
                    
                # Check if this is the right module by index
                module_info_file = module_dir / "section_info.json"
                if module_info_file.exists():
                    with open(module_info_file, "r") as f:
                        module_info = json.load(f)
                    print(f"📁 Checking module: {module_info.get('name')} (index: {module_info.get('index')})")
                    if module_info.get("index") == module_idx:
                        print(f"✅ Found correct module: {module_info.get('name')}")
                        # Found the right module, look for submodule
                        for submodule_dir in module_dir.glob("submodule_*"):
                            if not submodule_dir.is_dir():
                                continue
                                
                            submodule_info_file = submodule_dir / "subsection_info.json"
                            if submodule_info_file.exists():
                                with open(submodule_info_file, "r") as f:
                                    submodule_info = json.load(f)
                                print(f"📁 Checking submodule: {submodule_info.get('name')} (index: {submodule_info.get('index')})")
                                if submodule_info.get("index") == submodule_idx:
                                    print(f"✅ Found correct submodule: {submodule_info.get('name')}")
                                    # Found the right submodule, look for lesson
                                    for lesson_dir in submodule_dir.glob("lesson_*"):
                                        if not lesson_dir.is_dir():
                                            continue
                                            
                                        concept_info_file = lesson_dir / "concept_info.json"
                                        if concept_info_file.exists():
                                            with open(concept_info_file, "r") as f:
                                                concept_info = json.load(f)
                                            print(f"📁 Checking lesson: {concept_info.get('name')} (index: {concept_info.get('index')})")
                                            if concept_info.get("index") == lesson_idx:
                                                print(f"✅ Found correct lesson: {concept_info.get('name')}")
                                                # Found the right lesson, return agenda
                                                agenda = concept_info.get("agenda", "")
                                                print(f"📄 Returning agenda: {agenda[:100]}...")
                                                return agenda
        except Exception as e:
            print(f"❌ Error in fallback method: {e}")
        
        print(f"❌ Could not find lesson agenda for {course_name} - Module {module_idx}, Submodule {submodule_idx}, Lesson {lesson_idx}")
        return None
    
    def save_detailed_lesson_plan(self, course_name: str, module_idx: int, submodule_idx: int, lesson_idx: int, detailed_plan: str) -> bool:
        """Save the detailed lesson plan for a specific lesson"""
        try:
            course_dir = self.base_dir / self._safe_name(course_name)
            
            # Use the same improved logic to find the lesson directory
            lesson_pattern = f"module_{module_idx:02d}_*/submodule_{submodule_idx:02d}_*/lesson_{lesson_idx:02d}_*"
            
            # Find the lesson directory
            for lesson_dir in course_dir.glob(lesson_pattern):
                if lesson_dir.is_dir() and (lesson_dir / "concept_info.json").exists():
                    # Save the detailed plan
                    with open(lesson_dir / "detailed_plan.txt", "w") as f:
                        f.write(detailed_plan)
                    
                    # Update the concept info to mark as completed
                    with open(lesson_dir / "concept_info.json", "r") as f:
                        concept_info = json.load(f)
                    
                    concept_info["completed"] = True
                    concept_info["detailed_plan"] = detailed_plan
                    concept_info["completed_at"] = datetime.now().isoformat()
                    
                    with open(lesson_dir / "concept_info.json", "w") as f:
                        json.dump(concept_info, f, indent=2)
                    
                    return True
            
            # Fallback: try to find by looking through the structure systematically
            for module_dir in course_dir.glob("module_*"):
                if not module_dir.is_dir():
                    continue
                    
                module_info_file = module_dir / "section_info.json"
                if module_info_file.exists():
                    with open(module_info_file, "r") as f:
                        module_info = json.load(f)
                    if module_info.get("index") == module_idx:
                        for submodule_dir in module_dir.glob("submodule_*"):
                            if not submodule_dir.is_dir():
                                continue
                                
                            submodule_info_file = submodule_dir / "subsection_info.json"
                            if submodule_info_file.exists():
                                with open(submodule_info_file, "r") as f:
                                    submodule_info = json.load(f)
                                if submodule_info.get("index") == submodule_idx:
                                    for lesson_dir in submodule_dir.glob("lesson_*"):
                                        if not lesson_dir.is_dir():
                                            continue
                                            
                                        concept_info_file = lesson_dir / "concept_info.json"
                                        if concept_info_file.exists():
                                            with open(concept_info_file, "r") as f:
                                                concept_info = json.load(f)
                                            if concept_info.get("index") == lesson_idx:
                                                # Save the detailed plan
                                                with open(lesson_dir / "detailed_plan.txt", "w") as f:
                                                    f.write(detailed_plan)
                                                
                                                # Update the concept info to mark as completed
                                                concept_info["completed"] = True
                                                concept_info["detailed_plan"] = detailed_plan
                                                concept_info["completed_at"] = datetime.now().isoformat()
                                                
                                                with open(lesson_dir / "concept_info.json", "w") as f:
                                                    json.dump(concept_info, f, indent=2)
                                                
                                                return True
            
            return False
        except Exception as e:
            print(f"Error saving detailed lesson plan: {e}")
            return False
    
    def get_detailed_lesson_plan(self, course_name: str, module_idx: int, submodule_idx: int, lesson_idx: int) -> Optional[str]:
        """Get the detailed lesson plan for a specific lesson"""
        course_dir = self.base_dir / self._safe_name(course_name)
        
        # Use the same improved logic to find the lesson directory
        lesson_pattern = f"module_{module_idx:02d}_*/submodule_{submodule_idx:02d}_*/lesson_{lesson_idx:02d}_*"
        
        # Find the detailed plan file
        for lesson_dir in course_dir.glob(lesson_pattern):
            if lesson_dir.is_dir():
                plan_file = lesson_dir / "detailed_plan.txt"
                if plan_file.exists():
                    with open(plan_file, "r") as f:
                        return f.read().strip()
        
        # Fallback: try to find by looking through the structure systematically
        try:
            for module_dir in course_dir.glob("module_*"):
                if not module_dir.is_dir():
                    continue
                    
                module_info_file = module_dir / "section_info.json"
                if module_info_file.exists():
                    with open(module_info_file, "r") as f:
                        module_info = json.load(f)
                    if module_info.get("index") == module_idx:
                        for submodule_dir in module_dir.glob("submodule_*"):
                            if not submodule_dir.is_dir():
                                continue
                                
                            submodule_info_file = submodule_dir / "subsection_info.json"
                            if submodule_info_file.exists():
                                with open(submodule_info_file, "r") as f:
                                    submodule_info = json.load(f)
                                if submodule_info.get("index") == submodule_idx:
                                    for lesson_dir in submodule_dir.glob("lesson_*"):
                                        if not lesson_dir.is_dir():
                                            continue
                                            
                                        concept_info_file = lesson_dir / "concept_info.json"
                                        if concept_info_file.exists():
                                            with open(concept_info_file, "r") as f:
                                                concept_info = json.load(f)
                                            if concept_info.get("index") == lesson_idx:
                                                plan_file = lesson_dir / "detailed_plan.txt"
                                                if plan_file.exists():
                                                    with open(plan_file, "r") as f:
                                                        return f.read().strip()
        except Exception as e:
            print(f"Error finding detailed lesson plan: {e}")
        
        return None
    
    def get_course_progress(self, course_name: str) -> Dict[str, Any]:
        """Get the progress summary for a course"""
        course_dir = self.base_dir / self._safe_name(course_name)
        
        if not course_dir.exists():
            return {"error": "Course not found"}
        
        progress = {
            "course_name": course_name,
            "total_lessons": 0,
            "completed_lessons": 0,
            "total_time_minutes": 0,
            "modules": []
        }
        
        total_lessons = 0
        completed_lessons = 0
        total_time_minutes = 0
        
        for module_dir in sorted(course_dir.glob("module_*")):
            if not module_dir.is_dir():
                continue
                
            module_info_file = module_dir / "section_info.json"
            if not module_info_file.exists():
                continue
                
            with open(module_info_file, "r") as f:
                module_info = json.load(f)
            
            module_progress = {
                "name": module_info["name"],
                "index": module_info["index"],
                "submodules": []
            }
            
            for submodule_dir in sorted(module_dir.glob("submodule_*")):
                if not submodule_dir.is_dir():
                    continue
                    
                submodule_info_file = submodule_dir / "subsection_info.json"
                if not submodule_info_file.exists():
                    continue
                    
                with open(submodule_info_file, "r") as f:
                    submodule_info = json.load(f)
                
                submodule_progress = {
                    "name": submodule_info["name"],
                    "index": submodule_info["index"],
                    "lessons": []
                }
                
                for lesson_dir in sorted(submodule_dir.glob("lesson_*")):
                    if not lesson_dir.is_dir():
                        continue
                        
                    concept_info_file = lesson_dir / "concept_info.json"
                    if not concept_info_file.exists():
                        continue
                        
                    with open(concept_info_file, "r") as f:
                        concept_info = json.load(f)
                    
                    total_lessons += 1
                    if concept_info.get("completed", False):
                        completed_lessons += 1
                    
                    # Add time spent to total
                    lesson_time = concept_info.get("total_time_minutes", 0)
                    if lesson_time:
                        total_time_minutes += lesson_time
                    
                    submodule_progress["lessons"].append({
                        "name": concept_info["name"],
                        "index": concept_info["index"],
                        "completed": concept_info.get("completed", False),
                        "agenda": concept_info["agenda"],
                        "time_spent_minutes": lesson_time
                    })
                
                module_progress["submodules"].append(submodule_progress)
            
            progress["modules"].append(module_progress)
        
        progress["total_lessons"] = total_lessons
        progress["completed_lessons"] = completed_lessons
        progress["total_time_minutes"] = total_time_minutes
        progress["completion_percentage"] = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        return progress
    
    def list_courses(self) -> List[str]:
        """List all available courses"""
        courses = []
        for course_dir in self.base_dir.iterdir():
            if course_dir.is_dir() and (course_dir / "course_structure.json").exists():
                courses.append(course_dir.name)
        return courses
    
    def _safe_name(self, name: str) -> str:
        """Convert name to safe directory name"""
        return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_')[:50]
    
    def mark_lesson_completed(self, course_name: str, module_idx: int, submodule_idx: int, lesson_idx: int) -> bool:
        """Mark a lesson as completed"""
        try:
            lesson_dir = self._get_lesson_directory(course_name, module_idx, submodule_idx, lesson_idx)
            if not lesson_dir:
                return False
            
            concept_info_file = lesson_dir / "concept_info.json"
            if not concept_info_file.exists():
                return False
            
            # Read current info
            with open(concept_info_file, "r") as f:
                concept_info = json.load(f)
            
            # Mark as completed
            concept_info["completed"] = True
            concept_info["completed_at"] = datetime.now().isoformat()
            
            # Save updated info
            with open(concept_info_file, "w") as f:
                json.dump(concept_info, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error marking lesson as completed: {e}")
            return False
    
    def save_lesson_code(self, course_name: str, module_idx: int, submodule_idx: int, lesson_idx: int, code_content: str) -> bool:
        """Save the code content for a lesson"""
        try:
            lesson_dir = self._get_lesson_directory(course_name, module_idx, submodule_idx, lesson_idx)
            if not lesson_dir:
                return False
            
            # Save code to a file
            code_file = lesson_dir / "student_code.txt"
            with open(code_file, "w") as f:
                f.write(code_content)
            
            # Update concept info to include code file reference
            concept_info_file = lesson_dir / "concept_info.json"
            if concept_info_file.exists():
                with open(concept_info_file, "r") as f:
                    concept_info = json.load(f)
                
                # Track session time
                current_time = datetime.now().isoformat()
                if "first_code_update" not in concept_info:
                    concept_info["first_code_update"] = current_time
                
                concept_info["code_file"] = "student_code.txt"
                concept_info["last_code_update"] = current_time
                
                # Calculate total time spent (in minutes)
                if "first_code_update" in concept_info and "last_code_update" in concept_info:
                    try:
                        first_update = datetime.fromisoformat(concept_info["first_code_update"].replace('Z', '+00:00'))
                        last_update = datetime.fromisoformat(concept_info["last_code_update"].replace('Z', '+00:00'))
                        time_diff = last_update - first_update
                        total_minutes = int(time_diff.total_seconds() / 60)
                        concept_info["total_time_minutes"] = total_minutes
                    except:
                        pass
                
                with open(concept_info_file, "w") as f:
                    json.dump(concept_info, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving lesson code: {e}")
            return False
    
    def is_lesson_completed(self, course_name: str, module_idx: int, submodule_idx: int, lesson_idx: int) -> bool:
        """Check if a lesson is marked as completed"""
        try:
            lesson_dir = self._get_lesson_directory(course_name, module_idx, submodule_idx, lesson_idx)
            if not lesson_dir:
                return False
            
            concept_info_file = lesson_dir / "concept_info.json"
            if not concept_info_file.exists():
                return False
            
            with open(concept_info_file, "r") as f:
                concept_info = json.load(f)
            
            return concept_info.get("completed", False)
            
        except Exception as e:
            print(f"Error checking lesson completion: {e}")
            return False
    
    def get_lesson_code(self, course_name: str, module_idx: int, submodule_idx: int, lesson_idx: int) -> Optional[str]:
        """Retrieve the saved code content for a lesson"""
        try:
            lesson_dir = self._get_lesson_directory(course_name, module_idx, submodule_idx, lesson_idx)
            if not lesson_dir:
                return None
            
            code_file = lesson_dir / "student_code.txt"
            if not code_file.exists():
                return None
            
            with open(code_file, "r") as f:
                return f.read()
                
        except Exception as e:
            print(f"Error retrieving lesson code: {e}")
            return None
    
    def get_lesson_time_spent(self, course_name: str, module_idx: int, submodule_idx: int, lesson_idx: int) -> Optional[int]:
        """Get the total time spent on a lesson in minutes"""
        try:
            lesson_dir = self._get_lesson_directory(course_name, module_idx, submodule_idx, lesson_idx)
            if not lesson_dir:
                return None
            
            concept_info_file = lesson_dir / "concept_info.json"
            if not concept_info_file.exists():
                return None
            
            with open(concept_info_file, "r") as f:
                concept_info = json.load(f)
            
            return concept_info.get("total_time_minutes")
                
        except Exception as e:
            print(f"Error getting lesson time spent: {e}")
            return None
    
    def _get_lesson_directory(self, course_name: str, module_idx: int, submodule_idx: int, lesson_idx: int) -> Optional[Path]:
        """Helper method to get the lesson directory path"""
        try:
            course_dir = self.base_dir / self._safe_name(course_name)
            if not course_dir.exists():
                return None
            
            # Find the module directory
            module_dir = None
            for md in course_dir.glob("module_*"):
                if md.is_dir():
                    section_info_file = md / "section_info.json"
                    if section_info_file.exists():
                        with open(section_info_file, "r") as f:
                            section_info = json.load(f)
                        if section_info.get("index") == module_idx:
                            module_dir = md
                            break
            
            if not module_dir:
                return None
            
            # Find the submodule directory
            submodule_dir = None
            for smd in module_dir.glob("submodule_*"):
                if smd.is_dir():
                    subsection_info_file = smd / "subsection_info.json"
                    if subsection_info_file.exists():
                        with open(subsection_info_file, "r") as f:
                            subsection_info = json.load(f)
                        if subsection_info.get("index") == submodule_idx:
                            submodule_dir = smd
                            break
            
            if not submodule_dir:
                return None
            
            # Find the lesson directory
            lesson_dir = None
            for ld in submodule_dir.glob("lesson_*"):
                if ld.is_dir():
                    concept_info_file = ld / "concept_info.json"
                    if concept_info_file.exists():
                        with open(concept_info_file, "r") as f:
                            concept_info = json.load(f)
                        if concept_info.get("index") == lesson_idx:
                            lesson_dir = ld
                            break
            
            return lesson_dir
            
        except Exception as e:
            print(f"Error getting lesson directory: {e}")
            return None
    
    def save_youtube_videos(self, course_name: str, module_idx: int, submodule_idx: int, lesson_idx: int, videos: List[Dict[str, Any]]) -> bool:
        """Save YouTube video data for a lesson"""
        try:
            lesson_dir = self._get_lesson_directory(course_name, module_idx, submodule_idx, lesson_idx)
            if not lesson_dir:
                return False
            
            # Save videos data
            videos_file = lesson_dir / "youtube_videos.json"
            with open(videos_file, "w") as f:
                json.dump(videos, f, indent=2)
            
            # Save individual transcript files
            for i, video in enumerate(videos):
                if video.get('transcript'):
                    transcript_file = lesson_dir / f"video_{i+1}_transcript.txt"
                    with open(transcript_file, "w") as f:
                        f.write(video['transcript'])
                
                if video.get('summary'):
                    summary_file = lesson_dir / f"video_{i+1}_summary.txt"
                    with open(summary_file, "w") as f:
                        f.write(video['summary'])
            
            # Update concept info to include YouTube videos reference
            concept_info_file = lesson_dir / "concept_info.json"
            if concept_info_file.exists():
                with open(concept_info_file, "r") as f:
                    concept_info = json.load(f)
                
                concept_info["youtube_videos"] = len(videos)
                concept_info["youtube_videos_file"] = "youtube_videos.json"
                
                with open(concept_info_file, "w") as f:
                    json.dump(concept_info, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving YouTube videos: {e}")
            return False
    
    def get_youtube_videos(self, course_name: str, module_idx: int, submodule_idx: int, lesson_idx: int) -> Optional[List[Dict[str, Any]]]:
        """Get YouTube video data for a lesson"""
        try:
            lesson_dir = self._get_lesson_directory(course_name, module_idx, submodule_idx, lesson_idx)
            if not lesson_dir:
                return None
            
            videos_file = lesson_dir / "youtube_videos.json"
            if not videos_file.exists():
                return None
            
            with open(videos_file, "r") as f:
                videos = json.load(f)
            
            return videos
            
        except Exception as e:
            print(f"Error getting YouTube videos: {e}")
            return None
    
    def has_youtube_videos(self, course_name: str, module_idx: int, submodule_idx: int, lesson_idx: int) -> bool:
        """Check if a lesson has YouTube videos"""
        try:
            lesson_dir = self._get_lesson_directory(course_name, module_idx, submodule_idx, lesson_idx)
            if not lesson_dir:
                return False
            
            videos_file = lesson_dir / "youtube_videos.json"
            return videos_file.exists()
            
        except Exception as e:
            print(f"Error checking YouTube videos: {e}")
            return False
