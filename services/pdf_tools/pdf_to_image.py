"""
تبدیل صفحات یک فایل PDF به تصویر (یک عکس به‌ازای هر صفحه).

چرا PyMuPDF (fitz) و نه pdf2image؟
pdf2image برای رندر کردن PDF به Poppler (یک ابزار سیستمی خارجی) نیاز دارد که
روی ویندوز باید جداگانه دانلود و به PATH اضافه شود - یک مرحله نصب اضافه و
مستعد خطا برای یک کاربر مبتدی. PyMuPDF کاملاً self-contained است: با یک
`pip install` معمولی کار می‌کند و نیازی به نصب جداگانه‌ای ندارد.
"""

import uuid
from pathlib import Path
from typing import List

import fitz  # PyMuPDF

from app.config import settings


def pdf_to_images(pdf_path: Path, dpi: int = 150) -> List[Path]:
    settings.download_dir.mkdir(exist_ok=True)

    document = fitz.open(pdf_path)
    zoom = dpi / 72  # 72 وضوح پایه PDF است
    matrix = fitz.Matrix(zoom, zoom)

    output_paths: List[Path] = []
    try:
        for page_number in range(len(document)):
            page = document.load_page(page_number)
            pixmap = page.get_pixmap(matrix=matrix)

            output_path = settings.download_dir / f"{uuid.uuid4().hex}_p{page_number + 1}.png"
            pixmap.save(output_path)
            output_paths.append(output_path)
    finally:
        document.close()

    return output_paths
