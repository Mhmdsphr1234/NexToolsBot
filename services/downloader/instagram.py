"""دانلودر Instagram (پست، ریلز، IGTV). یک لایه نازک روی هسته مشترک yt-dlp."""

from pathlib import Path

from services.downloader.base import download_with_ytdlp


async def download_instagram(url: str) -> Path:
    return await download_with_ytdlp(url)
