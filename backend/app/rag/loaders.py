"""
استخراج متن خام از فایل‌های آپلودشده.
دیتای این پروژه فقط فایل‌های TXT/MD فارسی است، بنابراین این ماژول
مخصوص همین فرمت‌ها ساده‌سازی شده (بدون وابستگی به pypdf/python-docx).

نکته‌ی مهم درباره‌ی فارسی: فایل‌های txt فارسی گاهی با انکودینگ‌های
غیر از UTF-8 ذخیره می‌شوند (مثلا وقتی از Notepad یا نرم‌افزارهای قدیمی
ویندوز export شده باشند: Windows-1256 یا UTF-16). تابع زیر چند انکودینگ
رایج را به ترتیب امتحان می‌کند تا متن به‌درستی و بدون خراب شدن حروف
فارسی خوانده شود.
"""

from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ترتیب اهمیت دارد: ابتدا انکودینگ‌های دقیق‌تر امتحان می‌شوند
CANDIDATE_ENCODINGS = ["utf-8-sig", "utf-8", "utf-16", "cp1256", "windows-1256"]


def load_txt(path: Path) -> str:
    raw_bytes = path.read_bytes()

    for encoding in CANDIDATE_ENCODINGS:
        try:
            return raw_bytes.decode(encoding)
        except (UnicodeDecodeError, UnicodeError):
            continue

    logger.warning(
        f"هیچ‌کدام از انکودینگ‌های شناخته‌شده برای فایل {path.name} جواب نداد؛ "
        "با نادیده‌گرفتن کاراکترهای نامعتبر (utf-8) خوانده می‌شود."
    )
    return raw_bytes.decode("utf-8", errors="ignore")


LOADERS = {
    ".txt": load_txt,
    ".md": load_txt,
}


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    loader = LOADERS.get(suffix)
    if loader is None:
        raise ValueError(
            f"فرمت فایل '{suffix}' پشتیبانی نمی‌شود. فرمت‌های مجاز: {list(LOADERS.keys())}"
        )
    logger.info(f"در حال استخراج متن از فایل: {path.name}")
    text = loader(path)
    if not text.strip():
        logger.warning(f"فایل {path.name} خالی است یا متنی در آن یافت نشد.")
    return text
