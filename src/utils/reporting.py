import os
import json
from typing import Dict


def save_concept_report(base_dir: str, course: str, module: str, concept: str, report: Dict) -> str:
    safe_course = course.strip().replace("/", "_")
    safe_module = module.strip().replace("/", "_")
    safe_concept = concept.strip().replace("/", "_")
    dir_path = os.path.join(base_dir, safe_course, safe_module)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, f"{safe_concept}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return file_path


