from pathlib import Path
from app.utils.logger import get_logger
from app.utils.pdf_converter import pdf_to_text

logger = get_logger(__name__)

CANDIDATE_ENCODINGS = ["utf-8-sig", "utf-8", "utf-16", "cp1256", "windows-1256"]

def load_txt(path: Path) -> str:
    raw_bytes = path.read_bytes()
    for encoding in CANDIDATE_ENCODINGS:
        try:
            return raw_bytes.decode(encoding)
        except (UnicodeDecodeError, UnicodeError):
            continue
    logger.warning(f"Could not decode {path.name}; falling back to utf-8 with errors ignored.")
    return raw_bytes.decode("utf-8", errors="ignore")

def load_pdf(path: Path) -> str:
    """Extract text from PDF using pdf_to_text."""
    try:
        return pdf_to_text(path, use_ocr=True)
    except Exception as e:
        logger.error(f"PDF conversion failed for {path.name}: {e}")
        raise ValueError(f"Failed to extract text from PDF: {e}")

LOADERS = {
    ".txt": load_txt,
    ".md": load_txt,
    ".pdf": load_pdf,
}

def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    loader = LOADERS.get(suffix)
    if loader is None:
        raise ValueError(
            f"Unsupported file format '{suffix}'. Allowed: {list(LOADERS.keys())}"
        )
    logger.info(f"Extracting text from: {path.name}")
    text = loader(path)
    if not text.strip():
        logger.warning(f"File {path.name} is empty or no text extracted.")
    return text