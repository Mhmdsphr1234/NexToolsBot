"""
نقطه ورود اصلی پروژه NexTools.

این فایل فقط مسئول موارد زیر است:
- راه‌اندازی Logging
- ساخت Bot و Dispatcher
- ثبت (include) روترهای مختلف
- شروع Polling (دریافت پیام‌های تلگرام)

هیچ منطق مربوط به قابلیت‌ها اینجا نوشته نشده؛ طبق معماری پروژه، این فایل
فقط "چسب" اتصال بخش‌های مختلف به هم است.
"""

import asyncio
import logging

from aiogram.types import ErrorEvent

from app.bot import create_bot, create_dispatcher
from app.config import settings
from app.logger import setup_logging
from handlers.router import router as main_router
from handlers.start import router as start_router

logger = logging.getLogger(__name__)


async def main() -> None:
    setup_logging()
    settings.download_dir.mkdir(exist_ok=True)

    bot = create_bot()
    dp = create_dispatcher()

    dp.include_router(start_router)
    dp.include_router(main_router)

    @dp.error()
    async def handle_global_error(event: ErrorEvent) -> None:
        """
        شبکه ایمنی نهایی: اگر هر Handler دیگری خطای پیش‌بینی‌نشده‌ای پرتاب کند،
        این تابع جلوی کرش کامل ربات را می‌گیرد، خطا را لاگ می‌کند و
        به کاربر یک پیام قابل‌فهم نشان می‌دهد.
        """
        logger.error("Unhandled exception in update handling", exc_info=event.exception)
        update = event.update
        if update.message:
            try:
                await update.message.answer(
                    "⚠️ یه خطای غیرمنتظره پیش اومد. لطفاً دوباره امتحان کن."
                )
            except Exception:  # noqa: BLE001
                pass

    logger.info("NexTools bot is starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger(__name__).info("Bot stopped manually.")
