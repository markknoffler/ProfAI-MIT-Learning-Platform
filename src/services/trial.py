"""
quick_course_test.py
--------------------
1. Open a new terminal.
2. If you want to test the REAL backend, make sure:
     • ollama serve          # running locally
     • ngrok http 11434      # tunnel up; copy the https URL
     • export NGROK_OLLAMA_URL="https://<your-id>.ngrok-free.app"
     • export OLLAMA_MODEL="llama3.1"   # or whatever you pulled
3. Run:  python quick_course_test.py
"""

import json
from course_service import generate_course_structure

def main() -> None:
    topic = "Data Structures"          # pick any topic
    print(f"Requesting course on: {topic!r}\n")

    course_json = generate_course_structure(user_id="demo_user", topic=topic)

    # Pretty-print just the top-level keys and first section for brevity
    print(">>> High-level keys returned:")
    print(list(course_json.keys()), "\n")

    print(">>> First section snippet:")
    first_section = course_json.get("sections", [{}])[0]
    print(json.dumps(first_section, indent=2))

if __name__ == "__main__":
    main()
