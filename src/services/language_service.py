import os
import json
import requests
from typing import Dict, Any, List, Optional
from youtube_transcript_api import YouTubeTranscriptApi
import re

class LanguageService:
    def __init__(self, ngrok_endpoint: str = "https://22c7a5135078.ngrok-free.app"):
        self.ngrok_endpoint = ngrok_endpoint
        self.youtube_api_key = "AIzaSyAdORMhAnuRhdvqi87os4YvmWjss6ENwuM"
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
            response = requests.post(
                f"{self.ngrok_endpoint}/api/generate",
                json={"prompt": prompt},
                timeout=120
            )
            response.raise_for_status()
            
            curriculum = response.json()
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
            response = requests.post(
                f"{self.ngrok_endpoint}/api/generate",
                json={"prompt": prompt},
                timeout=120
            )
            response.raise_for_status()
            
            expanded_lesson = response.json()
            
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
            response = requests.post(
                f"{self.ngrok_endpoint}/api/generate",
                json={"prompt": prompt},
                timeout=60
            )
            response.raise_for_status()
            
            search_data = response.json()
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
            response = requests.post(
                f"{self.ngrok_endpoint}/api/generate",
                json={"prompt": prompt},
                timeout=60
            )
            response.raise_for_status()
            
            return response.json().get("response", "Summary not available")
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
        
        Create:
        1. A story (30-40 sentences) that naturally incorporates target vocabulary and grammar
        2. Target words to focus on (underline these in the story)
        3. Translation of each sentence
        
        Return as JSON:
        {{
            "story": [
                {{
                    "sentence": "Original sentence with target words underlined",
                    "translation": "English translation",
                    "target_words": ["word1", "word2"]
                }}
            ],
            "lesson_focus": {{
                "grammar_points": ["point1", "point2"],
                "vocabulary": ["word1", "word2", "word3"],
                "cultural_notes": "cultural information"
            }}
        }}
        """
        
        try:
            response = requests.post(
                f"{self.ngrok_endpoint}/api/generate",
                json={"prompt": prompt},
                timeout=120
            )
            response.raise_for_status()
            
            lesson_content = response.json()
            
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
