import io
import logging

logger = logging.getLogger(__name__)

SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".doc"}

MAX_TEXT_CHARS = 60_000


def is_supported(mime_type: str | None, file_name: str | None) -> bool:
    if mime_type and mime_type in SUPPORTED_MIME_TYPES:
        return True
    if file_name:
        ext = "." + file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        return ext in SUPPORTED_EXTENSIONS
    return False


def extract_text(file_bytes: bytes, mime_type: str | None, file_name: str | None) -> str:
    ext = ""
    if file_name and "." in file_name:
        ext = "." + file_name.rsplit(".", 1)[-1].lower()

    is_pdf = mime_type == "application/pdf" or ext == ".pdf"
    is_txt = mime_type == "text/plain" or ext == ".txt"
    is_docx = (
        mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or ext in (".docx", ".doc")
    )

    if is_pdf:
        return _extract_pdf(file_bytes)
    if is_txt:
        return _extract_txt(file_bytes)
    if is_docx:
        return _extract_docx(file_bytes)

    raise ValueError(f"Unsupported document type: mime={mime_type}, ext={ext}")


def _extract_pdf(file_bytes: bytes) -> str:
    import pdfplumber
    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    full_text = "\n\n".join(text_parts)
    return _truncate(full_text)


def _extract_txt(file_bytes: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "cp1251", "latin-1"):
        try:
            return _truncate(file_bytes.decode(encoding))
        except UnicodeDecodeError:
            continue
    return _truncate(file_bytes.decode("utf-8", errors="replace"))


def _extract_docx(file_bytes: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return _truncate("\n\n".join(paragraphs))


def _truncate(text: str) -> str:
    if len(text) > MAX_TEXT_CHARS:
        return text[:MAX_TEXT_CHARS] + f"\n\n[... текст обрезан, показаны первые {MAX_TEXT_CHARS} символов]"
    return text
