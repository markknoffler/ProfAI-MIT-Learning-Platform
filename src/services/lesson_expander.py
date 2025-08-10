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
        
        # Create a more concise expansion prompt to avoid timeouts
        prompt = f"""Create a detailed lesson plan for a programming course.

Course: {course_name}
Module: {module_name}
Submodule: {submodule_name}
Agenda: {lesson_agenda}

Create a comprehensive lesson plan with these sections:

1. LEARNING OBJECTIVES
   - 3-5 specific, measurable objectives

2. LESSON STRUCTURE
   - Introduction (5-10 min)
   - Main Content (30-45 min)
   - Practice Activities (15-20 min)
   - Assessment (10-15 min)
   - Summary (5 min)

3. DETAILED CONTENT
   - Break down the concept into 3-5 parts
   - Include examples and explanations
   - Address common misconceptions

4. PRACTICE EXERCISES
   - 2-3 hands-on exercises
   - Code examples if applicable
   - Step-by-step instructions

5. ASSESSMENT
   - Questions to check understanding
   - Common mistakes to watch for

6. TROUBLESHOOTING
   - Common issues and solutions
   - Debugging tips if applicable

Be specific, practical, and actionable. Use clear headings and bullet points."""

        try:
            # Call the AI model to expand the lesson plan
            response = call_model([
                {"role": "system", "content": "You are an expert curriculum designer. Create comprehensive, detailed lesson plans that are practical and actionable. Focus on being thorough and specific."},
                {"role": "user", "content": prompt}
            ])
            
            return response.strip()
            
        except Exception as e:
            print(f"❌ AI lesson expansion failed: {str(e)}")
            # Return a fallback lesson plan to ensure YouTube processing can still work
            return self._create_fallback_lesson_plan(course_name, module_name, submodule_name, lesson_agenda)
    
    def _create_fallback_lesson_plan(self, course_name: str, module_name: str, submodule_name: str, lesson_agenda: str) -> str:
        """Create a fallback lesson plan when AI fails"""
        return f"""# {lesson_agenda}

## LEARNING OBJECTIVES
- Understand the core concepts of {lesson_agenda}
- Apply practical knowledge in real-world scenarios
- Develop problem-solving skills related to {lesson_agenda}

## LESSON STRUCTURE
- **Introduction (5-10 min)**: Overview and motivation
- **Main Content (30-45 min)**: Core concepts and explanations
- **Practice Activities (15-20 min)**: Hands-on exercises
- **Assessment (10-15 min)**: Check for understanding
- **Summary (5 min)**: Recap and next steps

## DETAILED CONTENT
### Core Concepts
- Fundamental principles of {lesson_agenda}
- Key terminology and definitions
- Important concepts to master

### Practical Examples
- Real-world applications
- Code examples (if applicable)
- Step-by-step demonstrations

### Common Misconceptions
- Typical mistakes to avoid
- Clarifications on complex topics

## PRACTICE EXERCISES
1. **Basic Exercise**: Simple application of concepts
2. **Intermediate Exercise**: More complex problem-solving
3. **Advanced Exercise**: Real-world scenario application

## ASSESSMENT
- Understanding check questions
- Common pitfalls to watch for
- Success criteria for the lesson

## TROUBLESHOOTING
- Common issues students face
- Solutions and workarounds
- Debugging tips and techniques

This lesson provides a comprehensive introduction to {lesson_agenda} with practical exercises and real-world applications."""
    
    def get_lesson_context(self, course_name: str, module_name: str, submodule_name: str, lesson_name: str) -> Dict[str, Any]:
        """Get the full context for a lesson to help with expansion"""
        return {
            "course_name": course_name,
            "module_name": module_name,
            "submodule_name": submodule_name,
            "lesson_name": lesson_name,
            "full_context": f"{course_name} - {module_name} - {submodule_name} - {lesson_name}"
        }
