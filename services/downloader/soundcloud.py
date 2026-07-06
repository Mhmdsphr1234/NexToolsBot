"""دانلودر SoundCloud. خروجی را به mp3 تبدیل می‌کند تا در تلگرام مثل فایل صوتی پخش شود."""

from pathlib import Path

from services.downloader.base import download_with_ytdlp


async def download_soundcloud(url: str) -> Path:
    extra_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    return await download_with_ytdlp(url, extra_opts=extra_opts)
