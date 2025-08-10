from typing import List

import io
from pypdf import PdfReader


def _read_pdf(file_bytes: bytes) -> str:
    text_parts: List[str] = []
    with io.BytesIO(file_bytes) as fh:
        reader = PdfReader(fh)
        for page in reader.pages:
            content = page.extract_text() or ""
            if content:
                text_parts.append(content)
    return "\n".join(text_parts)


def ingest_uploaded_files(files) -> str:
    if not files:
        return ""
    texts: List[str] = []
    for f in files:
        name = f.name.lower()
        data = f.read()
        if name.endswith(".pdf"):
            try:
                texts.append(_read_pdf(data))
            except Exception:
                pass
        elif name.endswith((".txt", ".md")):
            try:
                texts.append(data.decode("utf-8", errors="ignore"))
            except Exception:
                pass
    merged = "\n\n---\n\n".join([t for t in texts if t])
    return merged[:15000]


