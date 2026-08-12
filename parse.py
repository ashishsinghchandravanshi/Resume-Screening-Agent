from pathlib import Path
from docx import Document
from pypdf import PdfReader


def extract_text(filepath: str) -> str:
    ext = Path(filepath).suffix.lower()

    if ext == ".txt":
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    elif ext == ".docx":
        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)

    elif ext == ".pdf":
        reader = PdfReader(filepath)
        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    else:
        raise ValueError(f"Unsupported file type: {ext}")