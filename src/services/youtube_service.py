import json
import os
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from .ollama_client import call_model


class YouTubeService:
    def __init__(self):
        self.api_key = "AIzaSyAdORMhAnuRhdvqi87os4YvmWjss6ENwuM"
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
    
    def generate_search_prompts(self, lesson_plan: str) -> List[str]:
        """Generate 3 search prompts for YouTube videos based on the lesson plan"""
        try:
            prompt = f"""Based on this lesson plan, give me 3 search prompts for videos with content similar to this lesson plan.

Lesson Plan:
{lesson_plan}

Return ONLY a JSON array with exactly 3 search prompts as strings. Example format:
["search prompt 1", "search prompt 2", "search prompt 3"]

Make the prompts specific and relevant to the lesson content."""

            response = call_model([
                {"role": "system", "content": "You are a helpful assistant that generates YouTube search prompts. Return ONLY valid JSON arrays."},
                {"role": "user", "content": prompt}
            ])
            
            # Parse the JSON response
            try:
                prompts = json.loads(response)
                if isinstance(prompts, list) and len(prompts) == 3:
                    return prompts
                else:
                    print(f"Invalid response format: {response}")
                    return self._generate_fallback_prompts(lesson_plan)
            except json.JSONDecodeError:
                print(f"Failed to parse JSON response: {response}")
                return self._generate_fallback_prompts(lesson_plan)
                
        except Exception as e:
            print(f"Error generating search prompts: {e}")
            return self._generate_fallback_prompts(lesson_plan)
    
    def _generate_fallback_prompts(self, lesson_plan: str) -> List[str]:
        """Generate fallback search prompts if AI fails"""
        # Extract key terms from lesson plan
        words = lesson_plan.lower().split()
        key_terms = [word for word in words if len(word) > 4 and word.isalpha()][:5]
        
        return [
            f"{' '.join(key_terms[:2])} tutorial",
            f"{' '.join(key_terms[2:4])} programming",
            f"{' '.join(key_terms[:3])} examples"
        ]
    
    def search_youtube_videos(self, search_prompts: List[str]) -> List[Dict[str, Any]]:
        """Search YouTube for videos matching the search prompts"""
        videos = []
        
        for prompt in search_prompts:
            try:
                # Search for videos with medium filter
                search_response = self.youtube.search().list(
                    q=prompt,
                    part='id,snippet',
                    maxResults=1,
                    type='video',
                    videoDuration='medium'  # Filter for medium length videos
                ).execute()
                
                if search_response.get('items'):
                    video = search_response['items'][0]
                    video_id = video['id']['videoId']
                    video_info = {
                        'id': video_id,
                        'title': video['snippet']['title'],
                        'description': video['snippet']['description'],
                        'channel': video['snippet']['channelTitle'],
                        'published_at': video['snippet']['publishedAt'],
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'search_prompt': prompt
                    }
                    videos.append(video_info)
                    print(f"Found video: {video_info['title']}")
                else:
                    print(f"No videos found for prompt: {prompt}")
                    
            except Exception as e:
                print(f"Error searching for prompt '{prompt}': {e}")
                continue
        
        return videos
    
    def get_video_transcript(self, video_id: str) -> Optional[str]:
        """Get the transcript for a YouTube video"""
        try:
            # Try multiple languages: English, Hindi, and any available
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi', 'auto'])
            formatter = TextFormatter()
            transcript = formatter.format_transcript(transcript_list)
            return transcript
        except Exception as e:
            print(f"Error getting transcript for video {video_id}: {e}")
            return None
    
    def summarize_video(self, transcript: str, video_title: str) -> str:
        """Generate a summary of the video transcript using AI"""
        try:
            prompt = f"""Summarize this YouTube video transcript in a concise and educational way.

Video Title: {video_title}
Transcript:
{transcript[:3000]}  # Limit transcript length to avoid token limits

Provide a 2-3 paragraph summary that:
1. Captures the main concepts and key points
2. Highlights practical applications or examples
3. Makes it easy for students to understand the content
4. Connects to programming/computer science learning

Keep the summary educational and focused on learning value."""

            response = call_model([
                {"role": "system", "content": "You are an educational content summarizer. Create clear, concise summaries that help students learn."},
                {"role": "user", "content": prompt}
            ])
            
            return response.strip()
            
        except Exception as e:
            print(f"Error summarizing video: {e}")
            return f"Summary unavailable for {video_title}. Error: {str(e)}"
    
    def generate_video_explanation(self, video_title: str, video_url: str, lesson_context: str) -> str:
        """Generate an AI explanation for why this video is relevant to the lesson"""
        try:
            prompt = f"""Explain why this YouTube video is relevant to the current programming lesson.

Lesson Context: {lesson_context}
Video Title: {video_title}
Video URL: {video_url}

Provide a brief explanation (2-3 sentences) that:
1. Connects the video content to the lesson objectives
2. Explains what value the video adds to the learning experience
3. Helps students understand why they should watch this video

Keep it concise and educational."""

            response = call_model([
                {"role": "system", "content": "You are an educational content curator. Explain why specific videos are relevant to programming lessons."},
                {"role": "user", "content": prompt}
            ])
            
            return response.strip()
            
        except Exception as e:
            print(f"Error generating video explanation: {e}")
            return f"This video provides additional context and examples for the lesson content."
    
    def process_lesson_videos(self, lesson_plan: str) -> List[Dict[str, Any]]:
        """Complete pipeline: generate prompts, search videos, get transcripts, and summarize"""
        print("🎬 Starting YouTube video processing for lesson...")
        
        # Step 1: Generate search prompts
        print("🔍 Generating search prompts...")
        search_prompts = self.generate_search_prompts(lesson_plan)
        print(f"✅ Generated {len(search_prompts)} search prompts")
        
        # Step 2: Search for videos
        print("📺 Searching for YouTube videos...")
        videos = self.search_youtube_videos(search_prompts)
        print(f"✅ Found {len(videos)} videos")
        
        # Step 3: Get transcripts and summarize
        processed_videos = []
        for video in videos:
            print(f"📝 Processing video: {video['title']}")
            
            # Get transcript
            transcript = self.get_video_transcript(video['id'])
            if transcript:
                # Generate summary
                summary = self.summarize_video(transcript, video['title'])
                
                # Generate explanation for why this video is relevant
                explanation = self.generate_video_explanation(video['title'], video['url'], lesson_plan[:500])
                
                processed_video = {
                    **video,
                    'transcript': transcript,
                    'summary': summary,
                    'explanation': explanation
                }
                processed_videos.append(processed_video)
                print(f"✅ Processed video: {video['title']}")
            else:
                print(f"❌ Could not get transcript for: {video['title']}")
        
        print(f"🎉 Completed processing {len(processed_videos)} videos")
        return processed_videos
