import os
import json
import requests
from typing import Dict, Any, List, Optional
from youtube_transcript_api import YouTubeTranscriptApi
import re
from src.services.ollama_client import call_model

class LanguageService:
    def __init__(self, ngrok_endpoint: str = None):
        self.ngrok_endpoint = ngrok_endpoint or os.getenv("NGROK_OLLAMA_URL", "")
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY", "")
        self.languages_dir = "languages"
        
        # Create languages directory if it doesn't exist
        if not os.path.exists(self.languages_dir):
            os.makedirs(self.languages_dir)
    
    def generate_language_curriculum(self, language: str, user_details: str) -> Dict[str, Any]:
        """Generate a complete curriculum for the specified language."""
        prompt = f"""
        Generate a comprehensive language learning curriculum for {language}.
        
        User Details: {user_details}
        
        Create a curriculum with exactly 7 modules, each containing exactly 10 submodules, 
        and each submodule containing exactly 10 lessons. The curriculum should be progressive 
        and tailored to the user's background and challenges.
        
        Return the response as a strict JSON with this exact structure:
        {{
            "language": "{language}",
            "modules": [
                {{
                    "module_number": 1,
                    "module_title": "Module Title",
                    "submodules": [
                        {{
                            "submodule_number": 1,
                            "submodule_title": "Submodule Title",
                            "lessons": [
                                {{
                                    "lesson_number": 1,
                                    "lesson_title": "Lesson Title",
                                    "lesson_overview": "Brief description of what will be covered"
                                }}
                            ]
                        }}
                    ]
                }}
            ]
        }}
        
        Ensure the JSON is valid and complete without any truncation.
        """
        
        try:
            # Use the Ollama client instead of direct HTTP request
            messages = [
                {"role": "system", "content": "You are a language curriculum designer. Generate structured JSON responses for language learning curricula."},
                {"role": "user", "content": prompt}
            ]
            
            response_text = call_model(messages)
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response_text[start_idx:end_idx]
                    curriculum = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            except (json.JSONDecodeError, ValueError) as e:
                # If JSON parsing fails, create a basic curriculum structure
                print(f"Warning: Could not parse JSON response: {e}")
                print(f"Response text: {response_text[:500]}...")
                curriculum = self._create_fallback_curriculum(language, user_details)
            
            return curriculum
        except Exception as e:
            raise Exception(f"Failed to generate curriculum: {str(e)}")
    
    def create_curriculum_structure(self, curriculum: Dict[str, Any]) -> str:
        """Create the directory structure for the curriculum."""
        language = curriculum["language"]
        language_dir = os.path.join(self.languages_dir, language)
        
        if not os.path.exists(language_dir):
            os.makedirs(language_dir)
        
        for module in curriculum["modules"]:
            module_dir = os.path.join(language_dir, f"module_{module['module_number']:02d}_{module['module_title'].replace(' ', '_')}")
            if not os.path.exists(module_dir):
                os.makedirs(module_dir)
            
            for submodule in module["submodules"]:
                submodule_dir = os.path.join(module_dir, f"submodule_{submodule['submodule_number']:02d}_{submodule['submodule_title'].replace(' ', '_')}")
                if not os.path.exists(submodule_dir):
                    os.makedirs(submodule_dir)
                
                for lesson in submodule["lessons"]:
                    lesson_dir = os.path.join(submodule_dir, f"lesson_{lesson['lesson_number']:02d}_{lesson['lesson_title'].replace(' ', '_')}")
                    if not os.path.exists(lesson_dir):
                        os.makedirs(lesson_dir)
                    
                    # Create initial lesson overview file
                    lesson_file = os.path.join(lesson_dir, "lesson_overview.txt")
                    with open(lesson_file, 'w', encoding='utf-8') as f:
                        f.write(lesson["lesson_overview"])
        
        return language_dir
    
    def _create_fallback_curriculum(self, language: str, user_details: str) -> Dict[str, Any]:
        """Create a basic fallback curriculum when AI generation fails."""
        return {
            "language": language,
            "modules": [
                {
                    "module_number": 1,
                    "module_title": f"Introduction to {language}",
                    "submodules": [
                        {
                            "submodule_number": 1,
                            "submodule_title": "Basic Greetings",
                            "lessons": [
                                {
                                    "lesson_number": 1,
                                    "lesson_title": "Hello and Goodbye",
                                    "lesson_overview": "Learn basic greetings in " + language
                                },
                                {
                                    "lesson_number": 2,
                                    "lesson_title": "Introducing Yourself",
                                    "lesson_overview": "Learn how to introduce yourself in " + language
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    
    def _create_fallback_lesson(self, language: str, lesson_overview: str) -> Dict[str, Any]:
        """Create a basic fallback lesson when AI generation fails."""
        return {
            "lesson_title": f"Basic {language} Lesson",
            "learning_objectives": [f"Learn basic {language} concepts", "Practice fundamental skills"],
            "key_concepts": ["Basic vocabulary", "Simple grammar"],
            "grammar_points": ["Basic sentence structure", "Common patterns"],
            "vocabulary": ["Essential words", "Common phrases"],
            "practice_exercises": ["Vocabulary practice", "Grammar exercises"],
            "cultural_context": f"Introduction to {language} culture",
            "detailed_content": lesson_overview
        }
    
    def expand_lesson_plan(self, language: str, module_num: int, submodule_num: int, 
                          lesson_num: int, learning_history: str = "") -> Dict[str, Any]:
        """Expand a lesson plan with detailed content."""
        # Get the lesson path
        lesson_path = self._get_lesson_path(language, module_num, submodule_num, lesson_num)
        if not lesson_path:
            raise Exception("Lesson path not found")
        
        # Read existing lesson overview
        overview_file = os.path.join(lesson_path, "lesson_overview.txt")
        if os.path.exists(overview_file):
            with open(overview_file, 'r', encoding='utf-8') as f:
                lesson_overview = f.read()
        else:
            lesson_overview = "Basic lesson overview"
        
        prompt = f"""
        Expand the following lesson plan for learning {language}:
        
        Module: {module_num}
        Submodule: {submodule_num}
        Lesson: {lesson_num}
        Current Overview: {lesson_overview}
        
        Learning History: {learning_history}
        
        Provide a detailed lesson plan including:
        1. Learning objectives
        2. Key concepts to cover
        3. Grammar points
        4. Vocabulary focus
        5. Practice exercises
        6. Cultural context (if relevant)
        
        Return as JSON:
        {{
            "lesson_title": "Title",
            "learning_objectives": ["objective1", "objective2"],
            "key_concepts": ["concept1", "concept2"],
            "grammar_points": ["grammar1", "grammar2"],
            "vocabulary": ["word1", "word2"],
            "practice_exercises": ["exercise1", "exercise2"],
            "cultural_context": "cultural information",
            "detailed_content": "comprehensive lesson content"
        }}
        """
        
        try:
            # Use the Ollama client instead of direct HTTP request
            messages = [
                {"role": "system", "content": "You are a language lesson designer. Generate structured JSON responses for detailed lesson plans."},
                {"role": "user", "content": prompt}
            ]
            
            response_text = call_model(messages)
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response_text[start_idx:end_idx]
                    expanded_lesson = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            except (json.JSONDecodeError, ValueError) as e:
                # If JSON parsing fails, create a basic lesson structure
                print(f"Warning: Could not parse JSON response: {e}")
                print(f"Response text: {response_text[:500]}...")
                expanded_lesson = self._create_fallback_lesson(language, lesson_overview)
            
            # Save expanded lesson
            expanded_file = os.path.join(lesson_path, "expanded_lesson.json")
            with open(expanded_file, 'w', encoding='utf-8') as f:
                json.dump(expanded_lesson, f, indent=2, ensure_ascii=False)
            
            # Generate YouTube search prompts
            self._generate_youtube_videos(lesson_path, expanded_lesson)
            
            return expanded_lesson
        except Exception as e:
            raise Exception(f"Failed to expand lesson: {str(e)}")
    
    def _generate_youtube_videos(self, lesson_path: str, expanded_lesson: Dict[str, Any]) -> None:
        """Generate YouTube video search prompts and download transcripts."""
        prompt = f"""
        Based on this language lesson:
        {json.dumps(expanded_lesson, indent=2)}
        
        Generate exactly 3 search prompts for YouTube videos that would be helpful for this lesson.
        Return as JSON:
        {{
            "search_prompts": ["prompt1", "prompt2", "prompt3"]
        }}
        """
        
        try:
            # Use the Ollama client instead of direct HTTP request
            messages = [
                {"role": "system", "content": "You are a YouTube content finder. Generate structured JSON responses for video search prompts."},
                {"role": "user", "content": prompt}
            ]
            
            response_text = call_model(messages)
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response_text[start_idx:end_idx]
                    search_data = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            except (json.JSONDecodeError, ValueError) as e:
                # If JSON parsing fails, create basic search prompts
                print(f"Warning: Could not parse JSON response: {e}")
                search_data = {"search_prompts": [f"learn {language} basics", f"{language} tutorial", f"{language} for beginners"]}
            
            search_prompts = search_data.get("search_prompts", [])
            
            videos = []
            for i, search_prompt in enumerate(search_prompts):
                video_info = self._search_youtube_video(search_prompt)
                if video_info:
                    transcript = self._download_transcript(video_info["video_id"])
                    if transcript:
                        video_info["transcript"] = transcript
                        videos.append(video_info)
                        
                        # Save transcript
                        transcript_file = os.path.join(lesson_path, f"video_{i+1}_transcript.txt")
                        with open(transcript_file, 'w', encoding='utf-8') as f:
                            f.write(transcript)
            
            # Save video information
            videos_file = os.path.join(lesson_path, "youtube_videos.json")
            with open(videos_file, 'w', encoding='utf-8') as f:
                json.dump(videos, f, indent=2, ensure_ascii=False)
            
            # Generate summaries for each video
            for i, video in enumerate(videos):
                summary = self._generate_video_summary(video["transcript"], expanded_lesson)
                summary_file = os.path.join(lesson_path, f"video_{i+1}_summary.txt")
                with open(summary_file, 'w', encoding='utf-8') as f:
                    f.write(summary)
                    
        except Exception as e:
            print(f"Error generating YouTube videos: {str(e)}")
    
    def _search_youtube_video(self, search_query: str) -> Optional[Dict[str, Any]]:
        """Search YouTube for a video matching the query."""
        try:
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet",
                "q": search_query,
                "key": self.youtube_api_key,
                "maxResults": 1,
                "type": "video",
                "videoDuration": "medium"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get("items"):
                item = data["items"][0]
                return {
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                }
        except Exception as e:
            print(f"Error searching YouTube: {str(e)}")
        
        return None
    
    def _download_transcript(self, video_id: str) -> Optional[str]:
        """Download transcript for a YouTube video."""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([entry["text"] for entry in transcript_list])
            return transcript_text
        except Exception as e:
            print(f"Error downloading transcript: {str(e)}")
            return None
    
    def _generate_video_summary(self, transcript: str, lesson_context: Dict[str, Any]) -> str:
        """Generate a summary of the video transcript in context of the lesson."""
        prompt = f"""
        Summarize this YouTube video transcript in the context of this language lesson:
        
        Lesson Context: {json.dumps(lesson_context, indent=2)}
        
        Video Transcript: {transcript[:2000]}...
        
        Provide a concise summary highlighting how this video relates to the lesson objectives.
        """
        
        try:
            # Use the Ollama client instead of direct HTTP request
            messages = [
                {"role": "system", "content": "You are a video content summarizer. Provide concise summaries of educational content."},
                {"role": "user", "content": prompt}
            ]
            
            response_text = call_model(messages)
            return response_text
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def _get_lesson_path(self, language: str, module_num: int, submodule_num: int, lesson_num: int) -> Optional[str]:
        """Get the path to a specific lesson."""
        language_dir = os.path.join(self.languages_dir, language)
        if not os.path.exists(language_dir):
            return None
        
        # Find the module directory
        for module_dir in os.listdir(language_dir):
            if module_dir.startswith(f"module_{module_num:02d}"):
                module_path = os.path.join(language_dir, module_dir)
                
                # Find the submodule directory
                for submodule_dir in os.listdir(module_path):
                    if submodule_dir.startswith(f"submodule_{submodule_num:02d}"):
                        submodule_path = os.path.join(module_path, submodule_dir)
                        
                        # Find the lesson directory
                        for lesson_dir in os.listdir(submodule_path):
                            if lesson_dir.startswith(f"lesson_{lesson_num:02d}"):
                                return os.path.join(submodule_path, lesson_dir)
        
        return None
    
    def _create_fallback_lesson_content(self, language: str) -> Dict[str, Any]:
        """Create basic fallback lesson content when AI generation fails."""
        # Language-specific fallback content
        if language.lower() == "korean":
            return {
                "story": [
                    {
                        "sentence": "안녕하세요, 저는 **한국어**를 **배우고** 있습니다.",
                        "translation": "Hello, I am learning Korean.",
                        "target_words": ["한국어", "배우고"]
                    },
                    {
                        "sentence": "이것은 **기본적인** 한국어 **수업**입니다.",
                        "translation": "This is a basic Korean lesson.",
                        "target_words": ["기본적인", "수업"]
                    },
                    {
                        "sentence": "저는 **학생**이고 한국어를 **공부합니다**.",
                        "translation": "I am a student and I study Korean.",
                        "target_words": ["학생", "공부합니다"]
                    }
                ],
                "lesson_focus": {
                    "grammar_points": ["Basic sentence structure", "Simple present tense"],
                    "vocabulary": ["한국어", "배우고", "기본적인", "수업", "학생", "공부합니다"],
                    "cultural_notes": "Introduction to Korean culture and basic greetings"
                }
            }
        elif language.lower() == "japanese":
            return {
                "story": [
                    {
                        "sentence": "こんにちは、私は**日本語**を**勉強して**います。",
                        "translation": "Hello, I am studying Japanese.",
                        "target_words": ["日本語", "勉強して"]
                    },
                    {
                        "sentence": "これは**基本的な**日本語の**授業**です。",
                        "translation": "This is a basic Japanese lesson.",
                        "target_words": ["基本的な", "授業"]
                    }
                ],
                "lesson_focus": {
                    "grammar_points": ["Basic sentence structure", "Simple present tense"],
                    "vocabulary": ["日本語", "勉強して", "基本的な", "授業"],
                    "cultural_notes": "Introduction to Japanese culture and basic greetings"
                }
            }
        elif language.lower() == "russian":
            return {
                "story": [
                    {
                        "sentence": "Привет, я **изучаю** **русский** язык.",
                        "translation": "Hello, I am studying Russian.",
                        "target_words": ["изучаю", "русский"]
                    },
                    {
                        "sentence": "Это **базовый** **урок** русского языка.",
                        "translation": "This is a basic Russian lesson.",
                        "target_words": ["базовый", "урок"]
                    }
                ],
                "lesson_focus": {
                    "grammar_points": ["Basic sentence structure", "Simple present tense"],
                    "vocabulary": ["изучаю", "русский", "базовый", "урок"],
                    "cultural_notes": "Introduction to Russian culture and basic greetings"
                }
            }
        else:
            # Generic fallback for other languages
            return {
                "story": [
                    {
                        "sentence": f"Hello, I am learning {language}.",
                        "translation": f"Hello, I am learning {language}.",
                        "target_words": ["hello", "learning"]
                    },
                    {
                        "sentence": f"This is a basic {language} lesson.",
                        "translation": f"This is a basic {language} lesson.",
                        "target_words": ["basic", "lesson"]
                    }
                ],
                "lesson_focus": {
                    "grammar_points": ["Basic sentence structure", "Simple present tense"],
                    "vocabulary": ["hello", "learning", "basic", "lesson"],
                    "cultural_notes": f"Introduction to {language} culture and basic greetings"
                }
            }
    
    def generate_lesson_content(self, language: str, module_num: int, submodule_num: int, 
                               lesson_num: int, target_words: List[str] = None) -> Dict[str, Any]:
        """Generate lesson content with story, target words, and translations."""
        lesson_path = self._get_lesson_path(language, module_num, submodule_num, lesson_num)
        if not lesson_path:
            raise Exception("Lesson path not found")
        
        # Read expanded lesson for context
        expanded_file = os.path.join(lesson_path, "expanded_lesson.json")
        lesson_context = {}
        if os.path.exists(expanded_file):
            with open(expanded_file, 'r', encoding='utf-8') as f:
                lesson_context = json.load(f)
        
        prompt = f"""
        Create a language lesson for {language} with the following components:
        
        Lesson Context: {json.dumps(lesson_context, indent=2)}
        
        IMPORTANT: You MUST generate actual {language} text (using proper script like Hangul for Korean, Hiragana/Katakana for Japanese, Cyrillic for Russian, etc.) NOT English text.
        
        Create:
        1. A story (5-10 sentences) written in actual {language} script that naturally incorporates target vocabulary and grammar
        2. Target words to focus on (mark these with ** in the story)
        3. English translation of each sentence
        
        For example, if the language is Korean:
        - "sentence" should be: "안녕하세요, 저는 **한국어**를 **배우고** 있습니다."
        - "translation" should be: "Hello, I am learning Korean."
        - "target_words" should be: ["한국어", "배우고"]
        
        Return as JSON:
        {{
            "story": [
                {{
                    "sentence": "Actual {language} text with target words marked with **",
                    "translation": "English translation",
                    "target_words": ["actual_word1", "actual_word2"]
                }}
            ],
            "lesson_focus": {{
                "grammar_points": ["point1", "point2"],
                "vocabulary": ["actual_word1", "actual_word2", "actual_word3"],
                "cultural_notes": "cultural information"
            }}
        }}
        
        CRITICAL: The "sentence" field must contain actual {language} text, not English text.
        """
        
        try:
            # Use the Ollama client instead of direct HTTP request
            messages = [
                {"role": "system", "content": f"You are a {language} language content creator. You MUST generate actual {language} text using the proper script (Hangul for Korean, Hiragana/Katakana for Japanese, Cyrillic for Russian, etc.). NEVER return English text in the 'sentence' field - only return the actual {language} text with target words marked using **."},
                {"role": "user", "content": prompt}
            ]
            
            response_text = call_model(messages)
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response_text[start_idx:end_idx]
                    lesson_content = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            except (json.JSONDecodeError, ValueError) as e:
                # If JSON parsing fails, create basic lesson content
                print(f"Warning: Could not parse JSON response: {e}")
                print(f"Response text: {response_text[:500]}...")
                lesson_content = self._create_fallback_lesson_content(language)
            
            # Save lesson content
            content_file = os.path.join(lesson_path, "lesson_content.json")
            with open(content_file, 'w', encoding='utf-8') as f:
                json.dump(lesson_content, f, indent=2, ensure_ascii=False)
            
            return lesson_content
        except Exception as e:
            raise Exception(f"Failed to generate lesson content: {str(e)}")
    
    def get_available_languages(self) -> List[str]:
        """Get list of available languages with curricula."""
        if not os.path.exists(self.languages_dir):
            return []
        
        return [lang for lang in os.listdir(self.languages_dir) 
                if os.path.isdir(os.path.join(self.languages_dir, lang))]
    
    def get_language_curriculum(self, language: str) -> Optional[Dict[str, Any]]:
        """Get the curriculum structure for a language."""
        language_dir = os.path.join(self.languages_dir, language)
        if not os.path.exists(language_dir):
            return None
        
        # Reconstruct curriculum from directory structure
        curriculum = {
            "language": language,
            "modules": []
        }
        
        for module_dir in sorted(os.listdir(language_dir)):
            if module_dir.startswith("module_"):
                module_num = int(module_dir.split("_")[1])
                module_title = "_".join(module_dir.split("_")[2:])
                
                module_data = {
                    "module_number": module_num,
                    "module_title": module_title.replace("_", " "),
                    "submodules": []
                }
                
                module_path = os.path.join(language_dir, module_dir)
                for submodule_dir in sorted(os.listdir(module_path)):
                    if submodule_dir.startswith("submodule_"):
                        submodule_num = int(submodule_dir.split("_")[1])
                        submodule_title = "_".join(submodule_dir.split("_")[2:])
                        
                        submodule_data = {
                            "submodule_number": submodule_num,
                            "submodule_title": submodule_title.replace("_", " "),
                            "lessons": []
                        }
                        
                        submodule_path = os.path.join(module_path, submodule_dir)
                        for lesson_dir in sorted(os.listdir(submodule_path)):
                            if lesson_dir.startswith("lesson_"):
                                lesson_num = int(lesson_dir.split("_")[1])
                                lesson_title = "_".join(lesson_dir.split("_")[2:])
                                
                                # Read lesson overview
                                overview_file = os.path.join(submodule_path, lesson_dir, "lesson_overview.txt")
                                lesson_overview = ""
                                if os.path.exists(overview_file):
                                    with open(overview_file, 'r', encoding='utf-8') as f:
                                        lesson_overview = f.read()
                                
                                lesson_data = {
                                    "lesson_number": lesson_num,
                                    "lesson_title": lesson_title.replace("_", " "),
                                    "lesson_overview": lesson_overview
                                }
                                
                                submodule_data["lessons"].append(lesson_data)
                        
                        module_data["submodules"].append(submodule_data)
                
                curriculum["modules"].append(module_data)
        
        return curriculum
