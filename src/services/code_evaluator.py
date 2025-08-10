from typing import Literal

from .ollama_client import call_model


def evaluate_code_guidance(objective: str, code: str, language: str = "Python") -> str:
    """Ask the model to give targeted suggestions and warnings without code."""
    system = (
        "You are a strict code coach. Evaluate the student's code only against the current learning objective."
        " Provide short, actionable suggestions, checks, and warnings. Do NOT write code or provide full solutions."
    )
    user = (
        f"Learning objective: {objective}\n\nLanguage: {language}\n\n"
        f"Student code:\n" + code[:8000]
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    return call_model(messages)


def evaluate_summary(user_id: str, concept: str, student_summary: str) -> dict:
    """Evaluate a student's verbal summary of a concept and identify gaps in understanding."""
    system = (
        "You are an expert educator evaluating a student's understanding of a programming concept. "
        "Analyze the student's verbal summary and identify any gaps, misconceptions, or missing key points. "
        "Provide constructive feedback that helps the student improve their understanding."
    )
    user = (
        f"Concept: {concept}\n\n"
        f"Student's verbal summary: {student_summary}\n\n"
        f"Please evaluate this summary and provide:"
        f"\n1. A judgement of understanding (excellent, good, fair, needs improvement)"
        f"\n2. Specific gaps or misconceptions identified"
        f"\n3. Key points that should have been mentioned"
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
        "gaps": gaps[:5],  # Limit to 5 gaps
        "full_response": response,
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


