import os
import json
from typing import Dict, Any, List

import requests
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from .chroma_store import query_knowledge
from .ollama_client import call_model
from .course_storage import CourseStorage
from .lesson_expander import LessonExpander
from .youtube_service import YouTubeService

# Initialize storage and expander
course_storage = CourseStorage()
lesson_expander = LessonExpander()
# Initialize YouTube service lazily to avoid import errors
youtube_service = None


#API_BASE = os.getenv("NGROK_OLLAMA_URL", "").rstrip("/")
API_BASE = "NGROK_OLLAMA_URL"


def _is_configured() -> bool:
    return API_BASE.startswith("http")


def _safe_name(name: str) -> str:
    return "_".join(name.strip().split())


def _mock_course(topic: str) -> Dict[str, Any]:
    """Generate a proper 7x10x10 mock course structure"""
    # Create a proper 7x10x10 structure
    sections = []
    
    # Generate 7 sections
    for section_idx in range(7):
        section_name = f"Module {section_idx + 1}"
        if section_idx == 0:
            section_name = "Introduction & Fundamentals"
        elif section_idx == 1:
            section_name = "Core Concepts"
        elif section_idx == 2:
            section_name = "Advanced Topics"
        elif section_idx == 3:
            section_name = "Practical Applications"
        elif section_idx == 4:
            section_name = "Problem Solving"
        elif section_idx == 5:
            section_name = "Real-world Projects"
        elif section_idx == 6:
            section_name = "Advanced Techniques"
        
        subsections = []
        # Generate 10 subsections per section
        for sub_idx in range(10):
            sub_name = f"Submodule {sub_idx + 1}"
            if sub_idx == 0:
                sub_name = "Getting Started"
            elif sub_idx == 1:
                sub_name = "Basic Concepts"
            elif sub_idx == 2:
                sub_name = "Intermediate Skills"
            elif sub_idx == 3:
                sub_name = "Advanced Techniques"
            elif sub_idx == 4:
                sub_name = "Practical Examples"
            elif sub_idx == 5:
                sub_name = "Problem Solving"
            elif sub_idx == 6:
                sub_name = "Best Practices"
            elif sub_idx == 7:
                sub_name = "Common Pitfalls"
            elif sub_idx == 8:
                sub_name = "Performance Optimization"
            elif sub_idx == 9:
                sub_name = "Integration & Deployment"
            
            concepts = []
            # Generate 10 concepts per subsection
            for concept_idx in range(10):
                concept_name = f"Concept {concept_idx + 1}"
                agenda = f"Learn essential {topic} concepts and techniques for {sub_name.lower()}"
                
                if concept_idx == 0:
                    concept_name = "Foundation Principles"
                    agenda = f"Understand the fundamental principles of {topic} in {sub_name.lower()}"
                elif concept_idx == 1:
                    concept_name = "Core Implementation"
                    agenda = f"Implement core {topic} functionality for {sub_name.lower()}"
                elif concept_idx == 2:
                    concept_name = "Advanced Features"
                    agenda = f"Master advanced {topic} features for {sub_name.lower()}"
                elif concept_idx == 3:
                    concept_name = "Practical Application"
                    agenda = f"Apply {topic} knowledge to solve real problems in {sub_name.lower()}"
                elif concept_idx == 4:
                    concept_name = "Performance Analysis"
                    agenda = f"Analyze and optimize {topic} performance in {sub_name.lower()}"
                elif concept_idx == 5:
                    concept_name = "Error Handling"
                    agenda = f"Implement robust error handling for {topic} in {sub_name.lower()}"
                elif concept_idx == 6:
                    concept_name = "Testing & Debugging"
                    agenda = f"Test and debug {topic} code in {sub_name.lower()}"
                elif concept_idx == 7:
                    concept_name = "Documentation"
                    agenda = f"Create comprehensive documentation for {topic} in {sub_name.lower()}"
                elif concept_idx == 8:
                    concept_name = "Integration"
                    agenda = f"Integrate {topic} with other systems in {sub_name.lower()}"
                elif concept_idx == 9:
                    concept_name = "Deployment"
                    agenda = f"Deploy and maintain {topic} solutions in {sub_name.lower()}"
                
                concepts.append({"name": concept_name, "agenda": agenda})
            
            subsections.append({"name": sub_name, "concepts": concepts})
        
        sections.append({"name": section_name, "subsections": subsections})
    
    course_data = {
        "course": topic,
        "sections": sections
    }
    
    # Save the mock course to storage
    try:
        save_course_to_storage(course_data)
        print(f"✅ Mock course saved to storage for: {topic}")
    except Exception as e:
        print(f"❌ Error saving mock course to storage: {str(e)}")
    
    return course_data


def _test_ai_connection() -> bool:
    """Test if the AI connection is working properly."""
    try:
        test_prompt = "Respond with exactly this JSON: {\"test\": \"success\"}"
        response = call_model([
            {"role": "system", "content": "You are a test bot. Return exactly what the user asks for."},
            {"role": "user", "content": test_prompt}
        ])
        
        # Try to parse the response
        try:
            data = json.loads(response)
            if data.get("test") == "success":
                print("✅ AI connection test successful")
                return True
        except json.JSONDecodeError:
            pass
            
        print(f"❌ AI connection test failed. Response: {response[:200]}...")
        return False
        
    except Exception as e:
        print(f"❌ AI connection test error: {str(e)}")
        return False


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=6))
def generate_course_structure(user_id: str, topic: str) -> Dict[str, Any]:
    """Generate a 7x10x10 course structure using AI. Fallback: mock locally."""
    known = query_knowledge(topic, n_results=12)
    
    # Test AI connection first
    print(f"🔍 Testing AI connection for topic: {topic}")
    if not _test_ai_connection():
        print("❌ AI connection failed, using mock course structure")
        return _mock_course(topic)
    
    # Always try to use AI first, fallback to mock only if AI fails
    try:
        print(f"🤖 Generating AI course structure for: {topic}")
        # Use the AI model to generate course structure
        prompt = f"""Create a course structure for {topic} with 7 sections, each with 10 subsections, each with 10 concepts given that the user already has the knowledge of: {known}.

Return ONLY this JSON structure (no other text):
{{
  "course": "{topic}",
  "sections": [
    {{
      "name": "Section Name",
      "subsections": [
        {{
          "name": "Subsection Name",
          "concepts": [
            {{
              "name": "Concept Name",
              "agenda": "Brief learning objective"
            }}
          ]
        }}
      ]
    }}
  ]
}}

Keep names short and agendas concise. Focus on practical learning. answer only and only and only in json. just return a json"""
        
        response = call_model([
            {"role": "system", "content": "You are a curriculum designer. Return ONLY valid JSON with no additional text or formatting."},
            {"role": "user", "content": prompt}
        ])
        
        # Try to parse the JSON response
        try:
            # First try direct JSON parsing
            data = json.loads(response)
            if "sections" in data and isinstance(data["sections"], list):
                data.setdefault("course", topic)
                print(f"✅ AI-generated course structure for '{topic}'")  # Debug log
                # Save to persistent storage
                save_course_to_storage(data)
                return data
        except json.JSONDecodeError as e:
            print(f"Direct JSON parsing failed: {str(e)}")
            # If direct parsing fails, try to extract and fix JSON from the response
            try:
                import re
                # Look for JSON content between curly braces
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    print(f"Extracted JSON string length: {len(json_str)}")
                    print(f"JSON string preview: {json_str[:200]}...")
                    
                    # Try to fix common JSON truncation issues
                    if not json_str.strip().endswith('}'):
                        print("JSON appears to be truncated, attempting to fix...")
                        # Count opening and closing braces to see if we can balance them
                        open_braces = json_str.count('{')
                        close_braces = json_str.count('}')
                        
                        if open_braces > close_braces:
                            # Add missing closing braces
                            missing_braces = open_braces - close_braces
                            json_str += '}' * missing_braces
                            print(f"Added {missing_braces} missing closing braces")
                        
                        # Also try to close any incomplete objects
                        if json_str.count('[') > json_str.count(']'):
                            missing_brackets = json_str.count('[') - json_str.count(']')
                            json_str += ']' * missing_brackets
                            print(f"Added {missing_brackets} missing closing brackets")
                    
                    try:
                        data = json.loads(json_str)
                        if "sections" in data and isinstance(data["sections"], list):
                            data.setdefault("course", topic)
                            print(f"✅ AI-generated course structure for '{topic}' (fixed truncated JSON)")  # Debug log
                            # Save to persistent storage
                            save_course_to_storage(data)
                            return data
                    except json.JSONDecodeError as fix_error:
                        print(f"Fixed JSON still invalid: {str(fix_error)}")
                        print(f"Attempted to fix: {json_str[:500]}...")
                        
            except Exception as extract_error:
                print(f"JSON extraction failed: {str(extract_error)}")
            
            print(f"AI response couldn't be parsed as JSON: {str(e)[:100]}...")  # Debug log
            print(f"Raw AI response: {response[:500]}...")  # Debug log
            print("Falling back to mock course structure")  # Debug log
            pass # Keep the original logic for now
        
    except Exception as e:
        print(f"Error calling AI model: {str(e)[:100]}...")  # Debug log
        print("Falling back to mock course structure")  # Debug log
        pass # Keep the original logic for now
    
    # Try a simplified course structure as a last resort
    print("🔄 Attempting simplified course structure generation...")
    try:
        simple_prompt = f"""Create a course structure for {topic} with exactly 7 sections, each with exactly 10 subsections, each with exactly 10 concepts.

Return ONLY this JSON structure (no other text):
{{
  "course": "{topic}",
  "sections": [
    {{
      "name": "Section 1",
      "subsections": [
        {{
          "name": "Subsection 1",
          "concepts": [
            {{
              "name": "Concept 1",
              "agenda": "Learn basic concept"
            }}
          ]
        }}
      ]
    }}
  ]
}}

IMPORTANT: Generate ALL 7 sections with ALL 10 subsections each, and ALL 10 concepts each. Keep names and agendas very short to avoid truncation. Return ONLY valid JSON."""

        simple_response = call_model([
            {"role": "system", "content": "You are a curriculum designer. Generate the complete 7x10x10 structure. Return ONLY valid JSON with no additional text."},
            {"role": "user", "content": simple_prompt}
        ])
        
        try:
            simple_data = json.loads(simple_response)
            if "sections" in simple_data:
                print("✅ Simplified course structure generated successfully")
                print(f"📊 Simplified structure has {len(simple_data['sections'])} sections")
                # Ensure it has the right structure
                simple_data.setdefault("course", topic)
                # Save to persistent storage
                save_course_to_storage(simple_data)
                return simple_data
            else:
                print("❌ Simplified structure missing 'sections' key")
                print(f"📄 Simplified data keys: {list(simple_data.keys())}")
        except json.JSONDecodeError as json_error:
            print(f"❌ Simplified structure JSON parse failed: {str(json_error)}")
            print(f"📄 Raw simplified response: {simple_response[:500]}...")
            
    except Exception as simple_error:
        print(f"❌ Simplified generation failed: {str(simple_error)}")
    
    # Final fallback to mock
    print("🔄 Using mock course structure as final fallback")
    return _mock_course(topic)


def save_course_to_storage(course_data: Dict[str, Any]) -> str:
    """Save a generated course to persistent storage"""
    try:
        course_name = course_data.get("course", "Unknown Course")
        course_path = course_storage.create_course_structure(course_name, course_data)
        print(f"✅ Course saved to storage: {course_path}")
        return course_path
    except Exception as e:
        print(f"❌ Error saving course to storage: {str(e)}")
        return ""

def expand_lesson_plan(course_name: str, module_idx: int, submodule_idx: int, lesson_idx: int, user_id: str = "default") -> str:
    """Expand a lesson plan using AI with full context"""
    print(f"🚀 Starting lesson expansion for: {course_name} - Module {module_idx}, Submodule {submodule_idx}, Lesson {lesson_idx}")
    
    try:
        # Get the lesson agenda
        print("🔍 Getting lesson agenda...")
        agenda = course_storage.get_lesson_agenda(course_name, module_idx, submodule_idx, lesson_idx)
        if not agenda:
            error_msg = "Error: Could not find lesson agenda"
            print(f"❌ {error_msg}")
            return error_msg
        
        print(f"✅ Found agenda: {agenda[:100]}...")
        
        # Get course structure to find names
        print("🔍 Getting course structure...")
        course_data = course_storage.get_course_structure(course_name)
        if not course_data:
            error_msg = "Error: Could not find course structure"
            print(f"❌ {error_msg}")
            return error_msg
        
        print(f"✅ Found course structure with {len(course_data.get('sections', []))} sections")
        
        # Find the specific module, submodule, and lesson names by index
        module_name = ""
        submodule_name = ""
        lesson_name = ""
        
        sections = course_data.get("sections", [])
        if module_idx <= len(sections):
            section = sections[module_idx - 1]  # Convert to 0-based index
            module_name = section.get("name", "")
            print(f"✅ Found module: {module_name}")
            
            subsections = section.get("subsections", [])
            if submodule_idx <= len(subsections):
                subsection = subsections[submodule_idx - 1]  # Convert to 0-based index
                submodule_name = subsection.get("name", "")
                print(f"✅ Found submodule: {submodule_name}")
                
                concepts = subsection.get("concepts", [])
                if lesson_idx <= len(concepts):
                    concept = concepts[lesson_idx - 1]  # Convert to 0-based index
                    lesson_name = concept.get("name", "")
                    print(f"✅ Found lesson: {lesson_name}")
        
        if not all([module_name, submodule_name, lesson_name]):
            error_msg = "Error: Could not find lesson information"
            print(f"❌ {error_msg}")
            return error_msg
        
        print(f"🎯 Expanding lesson: {course_name} > {module_name} > {submodule_name} > {lesson_name}")
        
        # Expand the lesson plan
        print("🤖 Calling AI to expand lesson plan...")
        detailed_plan = lesson_expander.expand_lesson_plan(
            course_name, module_name, submodule_name, agenda, user_id
        )
        
        print(f"📝 AI returned plan of length: {len(detailed_plan) if detailed_plan else 0}")
        
        # Save the detailed plan
        if detailed_plan and not detailed_plan.startswith("Error"):
            print("💾 Saving detailed lesson plan...")
            success = course_storage.save_detailed_lesson_plan(course_name, module_idx, submodule_idx, lesson_idx, detailed_plan)
            if success:
                print("✅ Detailed lesson plan saved successfully")
                
                # Process YouTube videos after successful lesson plan expansion
                print("🎬 Starting YouTube video processing...")
                try:
                    videos = youtube_service.process_lesson_videos(detailed_plan)
                    if videos:
                        print(f"📺 Found and processed {len(videos)} videos")
                        youtube_success = course_storage.save_youtube_videos(course_name, module_idx, submodule_idx, lesson_idx, videos)
                        if youtube_success:
                            print("✅ YouTube videos saved successfully")
                        else:
                            print("❌ Failed to save YouTube videos")
                    else:
                        print("⚠️ No videos found or processed")
                except Exception as e:
                    print(f"❌ YouTube video processing failed: {e}")
            else:
                print("❌ Failed to save detailed lesson plan")
        else:
            print(f"❌ AI expansion failed: {detailed_plan}")
        
        return detailed_plan
        
    except Exception as e:
        error_msg = f"Error expanding lesson plan: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=6))
def evaluate_concept_code(user_id: str, concept: str, student_code: str, topic_hint: str = "") -> str:
    """Provide focused, real-time guidance based only on the core concept and student's current code."""
    try:
        # Extract only the core concept
        core_concept = concept.split('.')[0] if '.' in concept else concept
        core_concept = core_concept[:100]  # Limit to first 100 chars
        
        # Use AI to evaluate the code with minimal context
        prompt = f"""Core concept: {core_concept}
Student code:
{student_code[:2000]}

Provide 1-2 brief directional hints (no solutions). Focus on:
1. Is the student on the right track?
2. What's the next logical step?
3. Any critical errors to avoid?

Keep response under 30 words. Be encouraging but direct."""

        response = call_model([
            {"role": "system", "content": "You are a focused coding mentor. Look ONLY at the core problem and student's code. Provide brief, actionable hints."},
            {"role": "user", "content": prompt}
        ])
        
        return response
        
    except Exception as e:
        return f"Keep iterating on your approach. Focus on the core concept: {concept[:50]}"


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=6))
def evaluate_summary(user_id: str, concept: str, student_summary: str) -> Dict[str, Any]:
    """Evaluate student's verbal summary with focused analysis."""
    try:
        # Extract only the core concept
        core_concept = concept.split('.')[0] if '.' in concept else concept
        core_concept = core_concept[:100]  # Limit to first 100 chars
        
        # Use AI to evaluate the summary with minimal context
        prompt = f"""Core concept: {core_concept}
Student summary: {student_summary[:500]}

Return JSON with:
- "judgement": "excellent", "good", "fair", "poor"
- "gaps": [2-3 specific missing concepts]
- "notes": brief learning style observation

Keep analysis focused and actionable."""

        response = call_model([
            {"role": "system", "content": "You are a focused evaluator. Return compact JSON with keys: judgement, gaps, notes."},
            {"role": "user", "content": prompt}
        ])
        
        # Try to parse the JSON response
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        
        # If JSON parsing fails, return structured response
        return {
            "judgement": "evaluated", 
            "gaps": ["Could not parse AI response"], 
            "notes": response[:100]
        }
        
    except Exception as e:
        return {"judgement": "error", "gaps": ["AI evaluation failed"], "notes": str(e)[:100]}


def adapt_course_after_subsection(user_id: str, course_state: Dict[str, Any], performance_notes: str) -> Dict[str, Any]:
    """Optional: call backend to adapt future modules. Fallback: returns original state unchanged."""
    if not _is_configured():
        return course_state
    url = f"{API_BASE}/adapt_course"
    try:
        resp = requests.post(url, json={"user_id": user_id, "course_state": course_state, "notes": performance_notes}, timeout=180)
        if resp.status_code < 400:
            return resp.json() or course_state
    except Exception:
        pass
    return course_state


