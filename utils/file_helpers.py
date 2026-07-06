"""
توابع کمکی برای کار با فایل‌های موقت.

چون هر عملیات (دانلود، تبدیل PDF، OCR و ...) فایل‌های موقتی روی دیسک می‌سازد،
باید بعد از ارسال نتیجه به کاربر، این فایل‌ها پاک شوند؛ در غیر این صورت
پوشه downloads/ با گذشت زمان (و کاربران بیشتر) بی‌نهایت بزرگ می‌شود.
"""

import logging
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)


def cleanup_files(paths: Iterable[Path]) -> None:
    for path in paths:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            logger.warning("Could not delete temp file: %s", path)
