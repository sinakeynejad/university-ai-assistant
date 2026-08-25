#!/usr/bin/env python3
"""
Converts PDF to text using PyMuPDF (text layer) and EasyOCR (scanned pages).
This version returns the extracted text as a string.
"""

from pathlib import Path
import pymupdf
import numpy as np
import easyocr

DPI = 150

_reader = None

def get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(['fa', 'en'], gpu=False)
    return _reader

def pdf_to_text(pdf_path: Path, use_ocr: bool = True) -> str:
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = pymupdf.open(pdf_path)
    all_text = []

    try:
        for page_num in range(1, doc.page_count + 1):
            page = doc[page_num - 1]

            # Try to extract text layer
            raw_text = page.get_text("text")
            if raw_text and isinstance(raw_text, str) and raw_text.strip():
                all_text.append(f"===== صفحه {page_num} =====\n{raw_text.strip()}\n")
                continue

            # If no text layer and OCR is enabled
            if use_ocr:
                zoom = DPI / 72
                matrix = pymupdf.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=matrix, alpha=False)

                # Convert pixmap to numpy array
                if pix.n == 1:
                    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
                elif pix.n == 3:
                    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                else:  # RGBA
                    img_rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                    img_array = img_rgb[:, :, :3]

                # OCR returns a list of strings when detail=0
                result = get_reader().readtext(img_array, detail=0, paragraph=False)
                if result:
                    # Convert each item to string (safe if it's already a string)
                    page_text = "\n".join(str(item) for item in result)
                else:
                    page_text = ""
                all_text.append(f"===== صفحه {page_num} =====\n{page_text}\n")
    finally:
        doc.close()

    return "\n".join(all_text)