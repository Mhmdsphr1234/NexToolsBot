"""
ساخت نمونه‌های Bot و Dispatcher.

این فایل عمداً خیلی کوچک نگه داشته شده؛ فقط "هسته" ربات را می‌سازد.
هیچ منطق مربوط به قابلیت‌ها (دانلود، PDF، OCR و ...) اینجا نباید نوشته شود.
"""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings


def create_bot() -> Bot:
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    return Dispatcher()
