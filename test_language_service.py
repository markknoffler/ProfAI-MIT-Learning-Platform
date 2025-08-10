#!/usr/bin/env python3
"""
Test script for the language learning functionality
"""

import os
import json
from src.services.language_service import LanguageService
from src.services.language_chroma_store import LanguageChromaStore

def test_language_service():
    """Test the language service functionality."""
    print("Testing Language Service...")
    
    # Initialize services
    language_service = LanguageService()
    chroma_store = LanguageChromaStore()
    
    # Test 1: Check if languages directory exists
    print(f"Languages directory exists: {os.path.exists('languages')}")
    
    # Test 2: Get available languages (should be empty initially)
    available_languages = language_service.get_available_languages()
    print(f"Available languages: {available_languages}")
    
    # Test 3: Test ChromaDB functionality
    print("Testing ChromaDB functionality...")
    
    # Store a test query
    query_id = chroma_store.store_user_query(
        language="Korean",
        query="How do I conjugate verbs in Korean?",
        lesson_context="Basic grammar lesson",
        module=1,
        submodule=1,
        lesson=1
    )
    print(f"Stored query with ID: {query_id}")
    
    # Store test learning history
    history_id = chroma_store.store_learning_history(
        language="Korean",
        concept="Verb conjugation",
        difficulty_level="intermediate",
        user_feedback="I struggle with irregular verbs"
    )
    print(f"Stored learning history with ID: {history_id}")
    
    # Store test difficulty
    difficulty_id = chroma_store.store_difficulty(
        language="Korean",
        concept="Verb conjugation",
        difficulty_description="Irregular verb patterns are confusing",
        grammar_structure="irregular verbs",
        semantic_concept="verb conjugation"
    )
    print(f"Stored difficulty with ID: {difficulty_id}")
    
    # Test 4: Get relevant context
    relevant_context = chroma_store.get_relevant_context("Korean", "verb conjugation", n_results=3)
    print(f"Found {len(relevant_context)} relevant contexts")
    
    # Test 5: Create RAG prompt
    rag_prompt = chroma_store.create_rag_prompt("Korean", "How do I conjugate verbs?", 1, 1, 1)
    print(f"RAG prompt length: {len(rag_prompt)} characters")
    
    print("Language service tests completed successfully!")

if __name__ == "__main__":
    test_language_service()
