import io
from typing import Optional
from fastapi import UploadFile

async def _read_bytes(upload: UploadFile) -> bytes:
    return await upload.read()

def _extract_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        return ""
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages:
        text = page.extract_text() or ""
        parts.append(text)
    return "\n".join(parts)

def _extract_docx(data: bytes) -> str:
    try:
        import docx
    except Exception:
        return ""
    d = docx.Document(io.BytesIO(data))
    return "\n".join(p.text for p in d.paragraphs)

def _extract_doc(data: bytes) -> str:
    try:
        import textract
    except Exception:
        return ""
    try:
        text = textract.process(io.BytesIO(data), extension='doc')
        return text.decode('utf-8', errors='ignore')
    except Exception:
        return ""

async def extract_text_from_upload(upload: UploadFile) -> str:
    filename = (upload.filename or "").lower()
    data = await _read_bytes(upload)
    if filename.endswith(".pdf"):
        return _extract_pdf(data)
    if filename.endswith(".docx"):
        return _extract_docx(data)
    if filename.endswith(".doc"):
        return _extract_doc(data)
    return data.decode("utf-8", errors="ignore")
