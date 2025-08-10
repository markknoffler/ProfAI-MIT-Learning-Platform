import json
from typing import Dict, Any

from .ollama_client import call_model
from .chroma_store import query_knowledge


def _planner_system_prompt() -> str:
    return (
        "You are an expert CS instructor and curriculum designer."
        " You must output STRICT JSON only, no markdown, no comments."
        " The JSON schema is: {\n"
        "  objective: string,\n"
        "  prerequisites: string[],\n"
        "  milestones: array<{ title: string, goal: string, checks: string[] }>,\n"
        "  exercises: array<{ prompt: string, difficulty: 'easy'|'medium'|'hard' }>,\n"
        "  evaluations: string[],\n"
        "  scaffolding_tips: string[],\n"
        "  summary: string,\n"
        "  concept_map: object\n"
        " }"
        " Do not include code solutions. Focus on step-by-step learning."
    )


def generate_lesson_plan(user_request: str, uploaded_context: str, knowledge_store) -> Dict[str, Any]:
    prior_knowledge = "\n\n".join(query_knowledge(user_request, n_results=4))

    messages = [
        {"role": "system", "content": _planner_system_prompt()},
        {
            "role": "user",
            "content": (
                f"User wants to learn: {user_request}\n\n"
                f"Relevant prior knowledge (from user db):\n{prior_knowledge}\n\n"
                f"Uploaded context (may include excerpts):\n{uploaded_context}\n\n"
                "Generate the JSON lesson plan now."
            ),
        },
    ]

    raw = call_model(messages)
    try:
        plan = json.loads(raw)
    except Exception:
        # Attempt to extract JSON substring
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                plan = json.loads(raw[start : end + 1])
            except Exception:
                plan = {}
        else:
            plan = {}

    if not isinstance(plan, dict) or not plan.get("objective"):
        # Fallback minimal plan
        plan = {
            "objective": user_request,
            "prerequisites": ["basic programming concepts"],
            "milestones": [
                {"title": "Understand the basics", "goal": user_request, "checks": ["define key terms"]}
            ],
            "exercises": [{"prompt": f"Implement a small demo related to: {user_request}", "difficulty": "easy"}],
            "evaluations": ["Can the learner explain the concept and write a minimal program?"],
            "scaffolding_tips": ["Work incrementally", "Test often", "Avoid full solutions"],
            "summary": f"Introductory plan for {user_request}",
            "concept_map": {"nodes": [user_request], "edges": []},
        }

    return plan


