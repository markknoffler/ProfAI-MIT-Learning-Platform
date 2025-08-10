import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class SimpleLanguageStore:
    """A simplified language store that uses JSON files instead of ChromaDB to avoid embedding issues."""
    
    def __init__(self, data_directory: str = "languages_data"):
        self.data_directory = data_directory
        os.makedirs(data_directory, exist_ok=True)
        
        # Create subdirectories for different data types
        self.queries_dir = os.path.join(data_directory, "queries")
        self.history_dir = os.path.join(data_directory, "history")
        self.difficulties_dir = os.path.join(data_directory, "difficulties")
        self.context_dir = os.path.join(data_directory, "context")
        
        for dir_path in [self.queries_dir, self.history_dir, self.difficulties_dir, self.context_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    def _get_language_file(self, language: str, data_type: str) -> str:
        """Get the file path for a specific language and data type."""
        return os.path.join(getattr(self, f"{data_type}_dir"), f"{language}.json")
    
    def _load_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Load data from a JSON file."""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def _save_data(self, file_path: str, data: List[Dict[str, Any]]) -> None:
        """Save data to a JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def store_user_query(self, language: str, query: str, lesson_context: str = "", 
                        module: int = None, submodule: int = None, lesson: int = None) -> str:
        """Store a user query with context."""
        file_path = self._get_language_file(language, "queries")
        data = self._load_data(file_path)
        
        query_id = f"query_{datetime.now().timestamp()}"
        query_data = {
            "id": query_id,
            "query": query,
            "lesson_context": lesson_context,
            "module": module,
            "submodule": submodule,
            "lesson": lesson,
            "timestamp": datetime.now().isoformat()
        }
        
        data.append(query_data)
        self._save_data(file_path, data)
        
        return query_id
    
    def store_learning_history(self, language: str, concept: str, difficulty_level: str,
                              user_feedback: str = "", lesson_context: str = "") -> str:
        """Store learning history and user feedback."""
        file_path = self._get_language_file(language, "history")
        data = self._load_data(file_path)
        
        history_id = f"history_{datetime.now().timestamp()}"
        history_data = {
            "id": history_id,
            "concept": concept,
            "difficulty_level": difficulty_level,
            "user_feedback": user_feedback,
            "lesson_context": lesson_context,
            "timestamp": datetime.now().isoformat()
        }
        
        data.append(history_data)
        self._save_data(file_path, data)
        
        return history_id
    
    def store_difficulty(self, language: str, concept: str, difficulty_description: str,
                        grammar_structure: str = "", semantic_concept: str = "") -> str:
        """Store specific difficulties the user has encountered."""
        file_path = self._get_language_file(language, "difficulties")
        data = self._load_data(file_path)
        
        difficulty_id = f"difficulty_{datetime.now().timestamp()}"
        difficulty_data = {
            "id": difficulty_id,
            "concept": concept,
            "difficulty_description": difficulty_description,
            "grammar_structure": grammar_structure,
            "semantic_concept": semantic_concept,
            "timestamp": datetime.now().isoformat()
        }
        
        data.append(difficulty_data)
        self._save_data(file_path, data)
        
        return difficulty_id
    
    def store_lesson_context(self, language: str, lesson_content: str, 
                           module: int, submodule: int, lesson: int,
                           video_transcripts: List[str] = None) -> str:
        """Store lesson context and video transcripts."""
        file_path = self._get_language_file(language, "context")
        data = self._load_data(file_path)
        
        context_id = f"context_{datetime.now().timestamp()}"
        context_data = {
            "id": context_id,
            "lesson_content": lesson_content,
            "module": module,
            "submodule": submodule,
            "lesson": lesson,
            "video_transcripts": video_transcripts or [],
            "timestamp": datetime.now().isoformat()
        }
        
        data.append(context_data)
        self._save_data(file_path, data)
        
        return context_id
    
    def get_learning_history(self, language: str, concept: str = None) -> List[Dict[str, Any]]:
        """Get learning history for a specific language and optionally concept."""
        file_path = self._get_language_file(language, "history")
        data = self._load_data(file_path)
        
        if concept:
            return [item for item in data if item.get("concept") == concept]
        return data
    
    def get_user_difficulties(self, language: str, concept: str = None) -> List[Dict[str, Any]]:
        """Get user difficulties for a specific language and optionally concept."""
        file_path = self._get_language_file(language, "difficulties")
        data = self._load_data(file_path)
        
        if concept:
            return [item for item in data if item.get("concept") == concept]
        return data
    
    def get_lesson_context(self, language: str, module: int = None, 
                          submodule: int = None, lesson: int = None) -> List[Dict[str, Any]]:
        """Get lesson context for a specific language and lesson."""
        file_path = self._get_language_file(language, "context")
        data = self._load_data(file_path)
        
        filtered_data = data
        if module is not None:
            filtered_data = [item for item in filtered_data if item.get("module") == module]
        if submodule is not None:
            filtered_data = [item for item in filtered_data if item.get("submodule") == submodule]
        if lesson is not None:
            filtered_data = [item for item in filtered_data if item.get("lesson") == lesson]
        
        return filtered_data
    
    def get_relevant_context(self, language: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Get relevant context based on a query (simplified keyword matching)."""
        all_context = []
        
        # Get queries
        queries_file = self._get_language_file(language, "queries")
        queries = self._load_data(queries_file)
        for query_item in queries:
            all_context.append({
                "type": "query",
                "content": query_item.get("query", ""),
                "metadata": query_item
            })
        
        # Get difficulties
        difficulties_file = self._get_language_file(language, "difficulties")
        difficulties = self._load_data(difficulties_file)
        for diff_item in difficulties:
            all_context.append({
                "type": "difficulty",
                "content": diff_item.get("difficulty_description", ""),
                "metadata": diff_item
            })
        
        # Simple keyword matching
        query_lower = query.lower()
        relevant_items = []
        for item in all_context:
            content_lower = item["content"].lower()
            if any(word in content_lower for word in query_lower.split()):
                relevant_items.append(item)
        
        return relevant_items[:n_results]
    
    def create_rag_prompt(self, language: str, current_query: str, 
                         module: int = None, submodule: int = None, lesson: int = None) -> str:
        """Create a RAG-enhanced prompt using user history and context."""
        # Get relevant context
        relevant_context = self.get_relevant_context(language, current_query, n_results=10)
        
        # Get user difficulties
        difficulties = self.get_user_difficulties(language)
        
        # Get learning history
        history = self.get_learning_history(language)
        
        # Build context string
        context_parts = []
        
        if relevant_context:
            context_parts.append("Relevant Previous Context:")
            for ctx in relevant_context[:5]:  # Limit to top 5
                context_parts.append(f"- {ctx['type']}: {ctx['content'][:200]}...")
        
        if difficulties:
            context_parts.append("\nUser's Previous Difficulties:")
            for diff in difficulties[:3]:  # Limit to top 3
                context_parts.append(f"- {diff.get('concept', 'Unknown')}: {diff.get('difficulty_description', '')[:200]}...")
        
        if history:
            context_parts.append("\nLearning History:")
            for hist in history[:3]:  # Limit to top 3
                context_parts.append(f"- {hist.get('concept', 'Unknown')}: {hist.get('user_feedback', '')[:200]}...")
        
        context_string = "\n".join(context_parts) if context_parts else "No previous context available."
        
        # Create enhanced prompt
        enhanced_prompt = f"""
        Language: {language}
        Current Lesson: Module {module}, Submodule {submodule}, Lesson {lesson}
        
        User's Learning Context:
        {context_string}
        
        Current Query: {current_query}
        
        Please provide a personalized response that takes into account the user's learning history, 
        previous difficulties, and relevant context. If the user has struggled with specific 
        grammar structures or concepts in the past, suggest targeted resources or explanations 
        that address those specific challenges.
        """
        
        return enhanced_prompt
