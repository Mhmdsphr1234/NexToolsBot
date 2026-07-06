"""
رجیستری مرکزی دانلودرها.

این فایل تنها جایی است که "نوع سرویس" را به "تابع دانلودکننده مربوطه" وصل می‌کند.
افزودن سرویس جدید در آینده (مثلاً Twitter/X):
۱. یک فایل جدید در همین پوشه بسازید (مثلاً twitter.py)
۲. آن را اینجا import و به دیکشنری _REGISTRY اضافه کنید
هیچ فایل دیگری از پروژه نیازی به تغییر ندارد (اصل Open/Closed).
"""

from typing import Awaitable, Callable, Optional
from pathlib import Path

from utils.url_detector import ServiceType
from services.downloader.youtube import download_youtube
from services.downloader.instagram import download_instagram
from services.downloader.pinterest import download_pinterest
from services.downloader.soundcloud import download_soundcloud
from services.downloader.spotify import download_spotify

Downloader = Callable[[str], Awaitable[Path]]

_REGISTRY: dict[ServiceType, Downloader] = {
    ServiceType.YOUTUBE: download_youtube,
    ServiceType.INSTAGRAM: download_instagram,
    ServiceType.PINTEREST: download_pinterest,
    ServiceType.SOUNDCLOUD: download_soundcloud,
    ServiceType.SPOTIFY: download_spotify,
}


def get_downloader(service: ServiceType) -> Optional[Downloader]:
    return _REGISTRY.get(service)
