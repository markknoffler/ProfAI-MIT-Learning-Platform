import os
import json
from typing import List, Dict, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential_jitter


OLLAMA_URL = os.getenv("NGROK_OLLAMA_URL", "")  # e.g., https://abcd-xyz.ngrok.io
MODEL_NAME = os.getenv("OLLAMA_MODEL", "phi3:14b")


def _is_configured() -> bool:
    return OLLAMA_URL.startswith("http") and len(MODEL_NAME) > 0


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=8))
def call_model(messages: List[Dict[str, str]], stream: bool = False) -> str:
    """Call the Ollama chat endpoint via ngrok. Fallback to a local mock when not configured."""
    if not _is_configured():
        # Safe mock response
        return (
            "[Mock AI]\n"
            "- Set a clear objective\n- Break down the task\n- Write code in small steps\n- Test iteratively\n- Avoid copying full solutions"
        )

    # Handle case where URL already includes /api/chat
    base_url = OLLAMA_URL.rstrip("/")
    if base_url.endswith("/api/chat"):
        url = base_url
    else:
        url = base_url + "/api/chat"
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": stream,
        "options": {
            "temperature": 0.2,
            "num_predict": 8192,  # Increased for complete course structure
            "stop": ["```", "```json", "```\n"]  # Stop at common markdown markers
        },
    }
    headers = {"Content-Type": "application/json"}
    
    print(f"🌐 Calling AI model at: {url}")
    print(f"📝 Model: {MODEL_NAME}")
    print(f"💬 Messages: {len(messages)}")
    
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=180)
        print(f"📡 Response status: {resp.status_code}")
        
        if resp.status_code >= 400:
            print(f"❌ API Error: {resp.status_code} - {resp.text[:200]}")
            resp.raise_for_status()
            
        data = resp.json()
        print(f"📦 Response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

        # Ollama chat response shape: { "message": { "content": "..." }, ... }
        if isinstance(data, dict) and "message" in data and isinstance(data["message"], dict):
            content = data["message"].get("content", "")
            print(f"✅ Extracted content length: {len(content)}")
            return content
        # Some proxies return {"content": "..."}
        if isinstance(data, dict) and "content" in data:
            content = data.get("content", "")
            print(f"✅ Extracted content length: {len(content)}")
            return content
        # Fallback
        print(f"⚠️ Using fallback response format")
        #return json.dumps(data)[:2000]
        return json.dumps(data)[:2000]
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        raise
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode failed: {str(e)}")
        print(f"📄 Raw response: {resp.text[:500]}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        raise


def quick_answer(question: str, context: str = "") -> str:
    system = (
        "You are a concise tutor. Answer briefly and clearly. If asked for code, return only a short high-level explanation, not full code."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Context:\n{context[:3000]}\n\nQuestion: {question}"},
    ]
    return call_model(messages)


