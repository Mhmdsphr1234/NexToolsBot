"""
استخراج متن از تصویر (OCR) با پشتیبانی فارسی و انگلیسی.

چرا pytesseract + Tesseract-OCR؟
Tesseract یک موتور OCR متن‌باز و بالغ گوگل است که به‌طور رسمی از پکیج زبان
فارسی (fas) پشتیبانی می‌کند. تنها نکته مهم این است که خود برنامه Tesseract
باید جداگانه روی سیستم نصب شود (این یک برنامه است، نه فقط یک کتابخانه پایتون)
که در README مرحله نصبش کامل توضیح داده شده.
"""

from pathlib import Path

import pytesseract
from PIL import Image

from app.config import settings

# مسیر فایل اجرایی Tesseract از تنظیمات .env خوانده می‌شود
pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


def extract_text(image_path: Path) -> str:
    """
    متن داخل تصویر را استخراج می‌کند.
    lang="fas+eng" یعنی Tesseract همزمان به‌دنبال متن فارسی و انگلیسی می‌گردد،
    که برای بیشتر عکس‌های واقعی (که ترکیبی از هر دو زبان هستند) بهترین نتیجه را می‌دهد.
    """
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, lang="fas+eng")
    return text.strip()
