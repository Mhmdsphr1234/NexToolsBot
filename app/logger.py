"""
پیکربندی مرکزی Logging.

چرا لاگ‌گیری ساختاریافته لازم است؟
وقتی ربات روی VPS به‌صورت دائمی اجرا می‌شود، شما جلوی صفحه نیستید که خطاها را
با چشم ببینید. بدون لاگ، پیدا کردن علت کرش یا خطای یک کاربر تقریباً غیرممکن است.
اینجا هم در فایل (برای بررسی بعدی) و هم در کنسول (برای دیدن زنده هنگام توسعه)
لاگ می‌نویسیم.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import settings


def setup_logging() -> None:
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    formatter = logging.Formatter(log_format)

    # لاگ در فایل، با چرخش خودکار فایل بعد از ۵ مگابایت (تا لاگ‌ها بی‌نهایت بزرگ نشوند)
    file_handler = RotatingFileHandler(
        logs_dir / "bot.log",
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # لاگ در کنسول، برای دیدن زنده وضعیت ربات هنگام اجرای دستی
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # کتابخانه‌های شخص ثالث معمولاً لاگ‌های خیلی پرحجم و کم‌اهمیت تولید می‌کنند
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
