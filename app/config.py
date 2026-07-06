"""
مدیریت تنظیمات پروژه.

چرا pydantic-settings؟
- مقادیر را مستقیم از فایل .env می‌خواند و نوعشان را هم اعتبارسنجی می‌کند
  (مثلاً اگر MAX_FILE_SIZE_MB عدد نباشد، همین ابتدای اجرای برنامه خطای واضح می‌دهد،
  نه وسط پردازش یک فایل کاربر).
- یک نقطه واحد برای همه تنظیمات پروژه فراهم می‌کند؛ بقیه ماژول‌ها فقط
  `from app.config import settings` می‌کنند و نیازی به os.getenv پراکنده در کد نیست.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str
    tesseract_cmd: str = "tesseract"
    log_level: str = "INFO"
    download_dir: Path = Path("downloads")
    max_file_size_mb: int = 45


# نمونه‌ی Singleton که در کل پروژه استفاده می‌شود.
settings = Settings()
