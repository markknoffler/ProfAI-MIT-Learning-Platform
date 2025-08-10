import os
from typing import Optional, List, Dict

import chromadb
from chromadb.utils import embedding_functions


_CLIENT = None
_COLL = None


def _get_client() -> chromadb.PersistentClient:
    global _CLIENT
    if _CLIENT is None:
        db_dir = os.getenv("CHROMA_DB_DIR", "./chroma_db")
        os.makedirs(db_dir, exist_ok=True)
        _CLIENT = chromadb.PersistentClient(path=db_dir)
    return _CLIENT


def get_knowledge_store():
    global _COLL
    if _COLL is None:
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        )
        _COLL = _get_client().get_or_create_collection(
            name="user_knowledge", embedding_function=ef
        )
    return _COLL


def query_knowledge(query_text: str, n_results: int = 5) -> List[str]:
    coll = get_knowledge_store()
    if not query_text.strip():
        return []
    res = coll.query(query_texts=[query_text], n_results=n_results)
    docs = res.get("documents", [[]])[0]
    return [d for d in docs if d]


def upsert_learned_concept(concept: str, summary: str) -> None:
    if not concept:
        return
    coll = get_knowledge_store()
    doc_id = concept.strip().lower().replace(" ", "_")[:64]
    try:
        coll.upsert(ids=[doc_id], documents=[f"Concept: {concept}\nSummary: {summary}"])
    except Exception:
        # If there is an embedding issue or duplicate, swallow to not break UX
        pass


