"""
دانلودر Spotify.

⚠️ محدودیت فنی مهم (لطفاً حتماً بخوانید):
اسپاتیفای فایل‌های صوتی خود را با DRM (مدیریت حقوق دیجیتال) رمزنگاری می‌کند.
دانلود مستقیم و قانونی یک فایل mp3/ogg از سرورهای اسپاتیفای امکان‌پذیر نیست
و هیچ کتابخانه‌ای این کار را واقعاً انجام نمی‌دهد.

بهترین جایگزین فنی: از لینک اسپاتیفای فقط "متادیتا" (نام آهنگ، خواننده، آلبوم)
خوانده می‌شود، سپس همان آهنگ در YouTube جست‌وجو و از آنجا دانلود می‌شود.
این دقیقاً همان کاری است که ابزار متن‌باز spotdl انجام می‌دهد.

چرا اجرای spotdl به‌صورت subprocess (خط فرمان) و نه import مستقیم کلاس‌های داخلی‌اش؟
رابط خط فرمان (CLI) spotdl پایدار و مستندسازی‌شده است، در حالی که کلاس‌های
داخلی پایتونش ممکن است بین نسخه‌ها تغییر کنند. استفاده از CLI ریسک خراب شدن
پروژه بعد از یک آپدیت کتابخانه را کم می‌کند.
"""

import asyncio
import logging
import sys
import uuid
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class SpotifyDownloadError(Exception):
    """خطای مربوط به جست‌وجو یا دانلود آهنگ اسپاتیفای."""


async def download_spotify(url: str) -> Path:
    settings.download_dir.mkdir(exist_ok=True)

    unique_prefix = uuid.uuid4().hex
    # الگوی نام‌گذاری خروجی spotdl: {artists} نام خواننده‌ها و {title} نام آهنگ است
    output_template = str(
        settings.download_dir / f"{unique_prefix}_{{title}}.{{output-ext}}"
    )

    command = [
        sys.executable,
        "-m",
        "spotdl",
        "download",
        url,
        "--output",
        output_template,
        "--format",
        "mp3",
    ]

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        logger.error(
            "spotdl failed for url=%s | stdout=%s | stderr=%s",
            url,
            stdout.decode(errors="ignore"),
            stderr.decode(errors="ignore"),
        )
        raise SpotifyDownloadError(
            "دانلود آهنگ اسپاتیفای ناموفق بود. ممکن است این آهنگ در YouTube پیدا نشده باشد."
        )

    # فایلی که با پیشوند unique_prefix شروع می‌شود را پیدا می‌کنیم
    matches = list(settings.download_dir.glob(f"{unique_prefix}_*.mp3"))
    if not matches:
        raise SpotifyDownloadError("دانلود انجام شد ولی فایل خروجی پیدا نشد.")

    return matches[0]
