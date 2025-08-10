from typing import Literal

from .ollama_client import call_model


def evaluate_code_guidance(objective: str, code: str, language: str = "Python") -> str:
    """Provide focused, real-time guidance based only on the core problem and student's current code."""
    system = (
        "You are a focused coding mentor. Look ONLY at the core problem/concept and the student's current code. "
        "Provide 1-2 brief, directional hints (no solutions). Focus on: "
        "1. Is the student on the right track? "
        "2. What's the next logical step? "
        "3. Any critical errors to avoid? "
        "Keep responses under 30 words. Be encouraging but direct."
    )
    
    # Extract only the core concept from the objective
    core_concept = objective.split('.')[0] if '.' in objective else objective
    core_concept = core_concept[:100]  # Limit to first 100 chars
    
    user = f"Core concept: {core_concept}\nStudent code:\n{code[:2000]}"
    
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    return call_model(messages)


def evaluate_summary(user_id: str, concept: str, student_summary: str) -> dict:
    """Evaluate a student's verbal summary with focused analysis."""
    # Extract only the core concept
    core_concept = concept.split('.')[0] if '.' in concept else concept
    core_concept = core_concept[:100]  # Limit to first 100 chars
    
    system = (
        "You are a focused educator evaluating understanding. "
        "Analyze the student's summary and provide concise, actionable feedback."
    )
    user = (
        f"Core concept: {core_concept}\n\n"
        f"Student summary: {student_summary[:500]}\n\n"
        f"Return JSON with:"
        f"\n- \"judgement\": \"excellent\", \"good\", \"fair\", \"poor\""
        f"\n- \"gaps\": [2-3 specific missing concepts]"
        f"\n- \"notes\": brief learning style observation"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    
    response = call_model(messages)
    
    # Parse the response to extract structured information
    judgement = "fair"  # default
    gaps = []
    
    # Simple parsing logic - in production, you might want more sophisticated parsing
    if "excellent" in response.lower():
        judgement = "excellent"
    elif "good" in response.lower():
        judgement = "good"
    elif "needs improvement" in response.lower() or "poor" in response.lower():
        judgement = "needs improvement"
    
    # Extract gaps (this is a simplified approach)
    lines = response.split('\n')
    for line in lines:
        if any(keyword in line.lower() for keyword in ['gap', 'missing', 'misconception', 'should', 'need']):
            gaps.append(line.strip())
    
    return {
        "judgement": judgement,
        "gaps": gaps[:3],  # Limit to 3 gaps
        "full_response": response[:200],  # Limit response length
        "user_id": user_id,
        "concept": concept,
        "evaluated_at": "2024-01-01T00:00:00Z"  # This would be actual timestamp in production
    }


def generate_learning_pattern(concept: str, objective: str, first_transcript: str, first_evaluation: str, second_transcript: str, second_evaluation: str) -> str:
    """Generate a 3-line learning pattern summary based on two voice evaluation attempts."""
    from .ollama_client import call_model
    
    system_prompt = (
        "You are an expert educational psychologist analyzing student learning patterns. "
        "Based on two voice evaluation attempts, generate exactly 3 lines summarizing: "
        "1. Learning behavior and persistence patterns "
        "2. Understanding capacity and improvement trajectory "
        "3. Specific learning habits and areas for development "
        "Keep each line concise and actionable."
    )
    
    user_prompt = f"""
    Concept: {concept}
    Learning Objective: {objective}
    
    First Attempt:
    - Transcript: {first_transcript}
    - Evaluation: {first_evaluation}
    
    Second Attempt:
    - Transcript: {second_transcript}
    - Evaluation: {second_evaluation}
    
    Generate exactly 3 lines summarizing the student's learning patterns, behavior, and capacity.
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    response = call_model(messages)
    
    # Ensure we get exactly 3 lines
    lines = response.strip().split('\n')
    if len(lines) >= 3:
        return '\n'.join(lines[:3])
    else:
        # Fallback if AI doesn't provide 3 lines
        return f"Student shows {'improvement' if 'improvement' in second_evaluation.lower() else 'consistent'} learning pattern for {concept}. Learning capacity appears {'strong' if 'excellent' in second_evaluation.lower() else 'developing'}. Focus on {'practice' if 'needs' in second_evaluation.lower() else 'application'} for continued growth."


