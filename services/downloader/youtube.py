"""دانلودر YouTube. یک لایه نازک روی هسته مشترک yt-dlp."""

from pathlib import Path

from services.downloader.base import download_with_ytdlp


async def download_youtube(url: str) -> Path:
    # حداکثر کیفیتی که هم ویدیو و هم صدا را با هم داشته باشد (بدون نیاز به merge سنگین)
    extra_opts = {"format": "best[ext=mp4]/best"}
    return await download_with_ytdlp(url, extra_opts=extra_opts)
