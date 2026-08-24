#!/usr/bin/env python3
"""
    Converts all PDFs in ../../data/raw/ to text files in ../../data/repaired_docs/
    using PyMuPDF for text extraction and EasyOCR for scanned pages.
    This Converter is optimized for persian literature
"""


from pathlib import Path
from typing import cast
import pymupdf
import numpy as np
import easyocr

DPI = 150


PROJECT_ROOT = Path(__file__).parent.resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "upload"
OUTPUT_DIR = PROJECT_ROOT / "data" / "repaired_docs"

reader = easyocr.Reader(['fa', 'en'], gpu=False)

def pdf_to_text(pdf_path, output_path):
   
    pdf_path = Path(pdf_path)
    output_path = Path(output_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"pdfrender: PDF not found: {pdf_path}")

    doc = pymupdf.open(pdf_path)
    total = doc.page_count

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            for page_num in range(1, total + 1):
             
                page = doc[page_num - 1]

                text = cast(str, page.get_text("text"))
                if text.strip():
                    print(f" pdfrender: Page {page_num} has text layer – skipping OCR")
                    f.write(f"\n\n===== صفحه {page_num} =====\n\n")
                    f.write(text.strip())
                    f.write("\n")
                    continue

              
                zoom = DPI / 72
                matrix = pymupdf.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=matrix, alpha=False)

                
                if pix.n == 1:
                    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
                elif pix.n == 3:
                    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                else:  # RGBA
                    img_rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                    img_array = img_rgb[:, :, :3]  # drop alpha

                result = cast(list[str], reader.readtext(img_array, detail=0, paragraph=False))

                if result:
                    page_text = "\n".join(result)
                    print(f"  pdfrender: Page {page_num}: found {len(result)} lines")
                else:
                    page_text = ""
                    print(f"   pdfrender: Page {page_num}: no text detected")

                f.write(f"\n\n===== صفحه {page_num} =====\n\n")
                f.write(page_text.strip())
                f.write("\n")
    finally:
        doc.close()

    

def process_single_pdf(pdf_path, output_dir=None):
  
    pdf_path = Path(pdf_path)
    if output_dir is None:
        output_dir = OUTPUT_DIR
    else:
        output_dir = Path(output_dir)

    output_filename = pdf_path.stem + ".txt"
    output_path = output_dir / output_filename

    if output_path.exists():
        print(f"Pdfrender:{output_path} has already been processed ")
        return

    pdf_to_text(pdf_path, output_path)

def process_all_pdfs(raw_dir=None, output_dir=None):
    
    if raw_dir is None:
        raw_dir = RAW_DIR
    else:
        raw_dir = Path(raw_dir)

    if output_dir is None:
        output_dir = OUTPUT_DIR
    else:
        output_dir = Path(output_dir)

    if not raw_dir.exists():
        print(f"pdfrender:Raw directory not found: {raw_dir}")
        return

    pdf_files = list(raw_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"pdfrender:No PDF files found in {raw_dir}")
        return

    print(f"pdfrender:Found {len(pdf_files)} PDF(s) in {raw_dir}")
    for pdf_file in pdf_files:
       
        try:
            process_single_pdf(pdf_file, output_dir)
        except Exception as e:
            print(f"pdfrender: Error processing {pdf_file.name}: {e}")

def main():
 
    process_all_pdfs()

if __name__ == "__main__":
    main()