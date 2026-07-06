"""
تبدیل یک یا چند عکس به یک فایل PDF.

چرا Pillow؟
Pillow استاندارد de-facto پردازش تصویر در پایتون است و به‌صورت built-in
قابلیت ذخیره چند تصویر در یک PDF چندصفحه‌ای را دارد (save_all + append_images)،
بدون نیاز به هیچ کتابخانه یا ابزار سیستمی اضافه.
"""

import uuid
from pathlib import Path
from typing import List

from PIL import Image

from app.config import settings


def images_to_pdf(image_paths: List[Path]) -> Path:
    if not image_paths:
        raise ValueError("هیچ عکسی برای تبدیل داده نشده است.")

    # حتماً به RGB تبدیل می‌کنیم چون PDF از حالت‌های رنگی مثل RGBA پشتیبانی نمی‌کند
    images = [Image.open(p).convert("RGB") for p in image_paths]

    settings.download_dir.mkdir(exist_ok=True)
    output_path = settings.download_dir / f"{uuid.uuid4().hex}.pdf"

    first_image, rest_images = images[0], images[1:]
    first_image.save(output_path, save_all=True, append_images=rest_images)

    return output_path
