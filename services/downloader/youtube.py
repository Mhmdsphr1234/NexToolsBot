"""دانلودر YouTube. یک لایه نازک روی هسته مشترک yt-dlp."""

from pathlib import Path

from services.downloader.base import download_with_ytdlp


async def download_youtube(url: str) -> Path:
    # تنظیمات هوشمند برای پشتیبانی از ویدیوهای معمولی و شورت بدون پر شدن رم رندر
    extra_opts = {
        # ۱. اولویت با ویدیوی حداکثر 720p (فرمت mp4) + بهترین صدا (فرمت m4a) است.
        # ۲. اگر جداگانه نبود، بهترین فایل سرهم‌شده‌ی زیر 720p را برمی‌دارد.
        "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best",
        
        # فرمت خروجی نهایی حتماً mp4 باشد تا تلگرام راحت آن را پخش کند
        "merge_output_format": "mp4",
        
        # اگر کاربر لینک ویدیو را از داخل یک پلی‌لیست کپی کرده بود، فقط همان ویدیو را دانلود کند نه کل پلی‌لیست را
        "noplaylist": True,
    }
    return await download_with_ytdlp(url, extra_opts=extra_opts)