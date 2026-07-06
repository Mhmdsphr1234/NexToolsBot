"""دانلودر Pinterest. یک لایه نازک روی هسته مشترک yt-dlp."""

from pathlib import Path

from services.downloader.base import download_with_ytdlp


async def download_pinterest(url: str) -> Path:
    return await download_with_ytdlp(url)
