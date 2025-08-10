import os
import chromadb
from chromadb.config import Settings
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

class LanguageChromaStore:
    def __init__(self, persist_directory: str = "src/services/chroma_db/languages"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create collections for different types of language data
        self.user_queries_collection = self.client.get_or_create_collection(
            name="language_user_queries",
            metadata={"description": "User queries and questions during language learning"}
        )
        
        self.learning_history_collection = self.client.get_or_create_collection(
            name="language_learning_history",
            metadata={"description": "User learning history and progress"}
        )
        
        self.difficulties_collection = self.client.get_or_create_collection(
            name="language_difficulties",
            metadata={"description": "User difficulties and challenges with specific concepts"}
        )
        
        self.lesson_context_collection = self.client.get_or_create_collection(
            name="language_lesson_context",
            metadata={"description": "Context from expanded lessons and video content"}
        )
    
    def store_user_query(self, language: str, query: str, lesson_context: str = "", 
                        module: int = None, submodule: int = None, lesson: int = None) -> str:
        """Store a user query with context."""
        metadata = {
            "language": language,
            "timestamp": datetime.now().isoformat(),
            "lesson_context": lesson_context,
            "module": module,
            "submodule": submodule,
            "lesson": lesson
        }
        
        document_id = f"query_{datetime.now().timestamp()}"
        
        self.user_queries_collection.add(
            documents=[query],
            metadatas=[metadata],
            ids=[document_id]
        )
        
        return document_id
    
    def store_learning_history(self, language: str, concept: str, difficulty_level: str,
                              user_feedback: str = "", lesson_context: str = "") -> str:
        """Store learning history and user feedback."""
        metadata = {
            "language": language,
            "concept": concept,
            "difficulty_level": difficulty_level,
            "timestamp": datetime.now().isoformat(),
            "lesson_context": lesson_context
        }
        
        document_id = f"history_{datetime.now().timestamp()}"
        
        self.learning_history_collection.add(
            documents=[user_feedback],
            metadatas=[metadata],
            ids=[document_id]
        )
        
        return document_id
    
    def store_difficulty(self, language: str, concept: str, difficulty_description: str,
                        grammar_structure: str = "", semantic_concept: str = "") -> str:
        """Store specific difficulties the user has encountered."""
        metadata = {
            "language": language,
            "concept": concept,
            "grammar_structure": grammar_structure,
            "semantic_concept": semantic_concept,
            "timestamp": datetime.now().isoformat()
        }
        
        document_id = f"difficulty_{datetime.now().timestamp()}"
        
        self.difficulties_collection.add(
            documents=[difficulty_description],
            metadatas=[metadata],
            ids=[document_id]
        )
        
        return document_id
    
    def store_lesson_context(self, language: str, lesson_content: str, 
                           module: int, submodule: int, lesson: int,
                           video_transcripts: List[str] = None) -> str:
        """Store lesson context and video transcripts for RAG."""
        metadata = {
            "language": language,
            "module": module,
            "submodule": submodule,
            "lesson": lesson,
            "timestamp": datetime.now().isoformat(),
            "has_videos": bool(video_transcripts)
        }
        
        # Combine lesson content with video transcripts
        full_content = lesson_content
        if video_transcripts:
            full_content += "\n\nVideo Transcripts:\n" + "\n".join(video_transcripts)
        
        document_id = f"lesson_{language}_{module}_{submodule}_{lesson}"
        
        self.lesson_context_collection.add(
            documents=[full_content],
            metadatas=[metadata],
            ids=[document_id]
        )
        
        return document_id
    
    def get_relevant_context(self, language: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Get relevant context from all collections for a query."""
        results = []
        
        # Search in user queries
        query_results = self.user_queries_collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"language": language}
        )
        
        for i, doc in enumerate(query_results['documents'][0]):
            results.append({
                "type": "user_query",
                "content": doc,
                "metadata": query_results['metadatas'][0][i]
            })
        
        # Search in learning history
        history_results = self.learning_history_collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"language": language}
        )
        
        for i, doc in enumerate(history_results['documents'][0]):
            results.append({
                "type": "learning_history",
                "content": doc,
                "metadata": history_results['metadatas'][0][i]
            })
        
        # Search in difficulties
        difficulty_results = self.difficulties_collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"language": language}
        )
        
        for i, doc in enumerate(difficulty_results['documents'][0]):
            results.append({
                "type": "difficulty",
                "content": doc,
                "metadata": difficulty_results['metadatas'][0][i]
            })
        
        # Search in lesson context
        lesson_results = self.lesson_context_collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"language": language}
        )
        
        for i, doc in enumerate(lesson_results['documents'][0]):
            results.append({
                "type": "lesson_context",
                "content": doc,
                "metadata": lesson_results['metadatas'][0][i]
            })
        
        return results
    
    def get_user_difficulties(self, language: str, concept: str = None) -> List[Dict[str, Any]]:
        """Get user difficulties for a specific language and optionally concept."""
        where_clause = {"language": language}
        if concept:
            where_clause["concept"] = concept
        
        results = self.difficulties_collection.get(where=where_clause)
        
        difficulties = []
        for i, doc in enumerate(results['documents']):
            difficulties.append({
                "content": doc,
                "metadata": results['metadatas'][i]
            })
        
        return difficulties
    
    def get_learning_history(self, language: str, concept: str = None) -> List[Dict[str, Any]]:
        """Get learning history for a specific language and optionally concept."""
        where_clause = {"language": language}
        if concept:
            where_clause["concept"] = concept
        
        results = self.learning_history_collection.get(where=where_clause)
        
        history = []
        for i, doc in enumerate(results['documents']):
            history.append({
                "content": doc,
                "metadata": results['metadatas'][i]
            })
        
        return history
    
    def get_lesson_context(self, language: str, module: int = None, 
                          submodule: int = None, lesson: int = None) -> List[Dict[str, Any]]:
        """Get lesson context for a specific language and lesson."""
        where_clause = {"language": language}
        if module is not None:
            where_clause["module"] = module
        if submodule is not None:
            where_clause["submodule"] = submodule
        if lesson is not None:
            where_clause["lesson"] = lesson
        
        results = self.lesson_context_collection.get(where=where_clause)
        
        contexts = []
        for i, doc in enumerate(results['documents']):
            contexts.append({
                "content": doc,
                "metadata": results['metadatas'][i]
            })
        
        return contexts
    
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
                context_parts.append(f"- {diff['metadata'].get('concept', 'Unknown')}: {diff['content'][:200]}...")
        
        if history:
            context_parts.append("\nLearning History:")
            for hist in history[:3]:  # Limit to top 3
                context_parts.append(f"- {hist['metadata'].get('concept', 'Unknown')}: {hist['content'][:200]}...")
        
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
    
    def suggest_targeted_resources(self, language: str, current_concept: str) -> List[Dict[str, Any]]:
        """Suggest targeted resources based on user difficulties."""
        # Get user difficulties related to the current concept
        difficulties = self.get_user_difficulties(language, current_concept)
        
        # Get lesson contexts that might be helpful
        lesson_contexts = self.get_lesson_context(language)
        
        suggestions = []
        
        # Look for lessons that address similar difficulties
        for diff in difficulties:
            for ctx in lesson_contexts:
                if any(keyword in ctx['content'].lower() for keyword in 
                      diff['metadata'].get('grammar_structure', '').lower().split()):
                    suggestions.append({
                        "type": "targeted_lesson",
                        "content": ctx['content'][:300] + "...",
                        "metadata": ctx['metadata'],
                        "reason": f"Addresses difficulty with {diff['metadata'].get('grammar_structure', 'concept')}"
                    })
        
        return suggestions[:5]  # Limit to 5 suggestions
