import json
from typing import Dict, Any, Optional
from .ollama_client import call_model
from .chroma_store import query_knowledge

class LessonExpander:
    def __init__(self):
        pass
    
    def expand_lesson_plan(self, course_name: str, module_name: str, submodule_name: str, lesson_agenda: str, user_id: str = "default") -> str:
        """Expand a basic lesson agenda into a detailed lesson plan using AI"""
        
        # Get relevant knowledge from ChromaDB
        relevant_knowledge = query_knowledge(f"{course_name} {module_name} {submodule_name}", n_results=10)
        
        # Create the expansion prompt
        prompt = f"""You are an expert curriculum designer creating a highly detailed lesson plan for a programming course.

COURSE CONTEXT:
- Course: {course_name}
- Module: {module_name}
- Submodule: {submodule_name}
- Basic Agenda: {lesson_agenda}

STUDENT CONTEXT:
Based on what the student already knows: {relevant_knowledge}

TASK:
Create a comprehensive, detailed lesson plan that breaks down every small detail that should be covered for this lesson. This will be stored as a text file and used by instructors and students.

REQUIRED SECTIONS:

1. LESSON OVERVIEW
   - Learning Objectives (3-5 specific, measurable objectives)
   - Prerequisites (what the student should know before this lesson)
   - Estimated Duration (total time needed)
   - Materials Needed (tools, software, resources)

2. LESSON STRUCTURE & TIMELINE
   - Introduction (5-10 minutes): Hook, overview, and motivation
   - Main Content (30-45 minutes): Core concepts and explanations
   - Practice Activities (15-20 minutes): Hands-on exercises
   - Assessment (10-15 minutes): Check for understanding
   - Summary & Next Steps (5 minutes): Recap and preview

3. DETAILED CONTENT BREAKDOWN
   Break down the main concept into 5-8 smaller, digestible parts:
   - For each part: What to teach, how to teach it, why it's important
   - Include specific examples and explanations
   - Address common misconceptions

4. PRACTICE EXERCISES
   - 3-5 hands-on exercises with increasing difficulty
   - Code examples if applicable
   - Real-world applications
   - Step-by-step instructions for each exercise

5. ASSESSMENT & EVALUATION
   - How to check if students understand each concept
   - Questions to ask students
   - Common mistakes to watch for
   - Success criteria for the lesson

6. DIFFERENTIATION & SUPPORT
   - How to support struggling students
   - How to challenge advanced students
   - Additional resources for different learning styles

7. TROUBLESHOOTING
   - Common issues students might face
   - How to help them overcome challenges
   - Debugging tips if applicable

8. CONNECTIONS & NEXT STEPS
   - How this lesson connects to previous material
   - What concepts this lesson prepares students for
   - Homework or follow-up activities

FORMAT REQUIREMENTS:
- Use clear headings for each section
- Use bullet points and numbered lists for clarity
- Be specific and actionable
- Write in a professional but accessible tone
- This should be comprehensive enough that another instructor could pick up this plan and teach the lesson effectively
- Focus on practical, actionable content that will help students truly master this concept

Remember: This is for a local AI model with no token limits, so be thorough and detailed. Create a lesson plan that covers every aspect of teaching this concept effectively."""

        try:
            # Call the AI model to expand the lesson plan
            response = call_model([
                {"role": "system", "content": "You are an expert curriculum designer. Create comprehensive, detailed lesson plans that are practical and actionable. Focus on being thorough and specific."},
                {"role": "user", "content": prompt}
            ])
            
            return response.strip()
            
        except Exception as e:
            return f"Error expanding lesson plan: {str(e)}"
    
    def get_lesson_context(self, course_name: str, module_name: str, submodule_name: str, lesson_name: str) -> Dict[str, Any]:
        """Get the full context for a lesson to help with expansion"""
        return {
            "course_name": course_name,
            "module_name": module_name,
            "submodule_name": submodule_name,
            "lesson_name": lesson_name,
            "full_context": f"{course_name} - {module_name} - {submodule_name} - {lesson_name}"
        }
