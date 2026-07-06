"""
این ماژول مسئول دو کار ساده است:
۱. پیدا کردن یک لینک داخل متن پیام کاربر
۲. تشخیص اینکه آن لینک متعلق به کدام سرویس است (یوتیوب، اینستاگرام و ...)

طراحی به‌صورت "Registry ساده" است: هر سرویس فقط یک الگوی regex دارد.
اضافه کردن یک سرویس جدید در آینده (مثلاً Twitter/X) یعنی فقط یک خط
به دیکشنری _PATTERNS اضافه می‌شود؛ نیازی به تغییر جای دیگری از کد نیست.
"""

import re
from enum import Enum, auto
from typing import Optional


class ServiceType(Enum):
    YOUTUBE = auto()
    INSTAGRAM = auto()
    PINTEREST = auto()
    SOUNDCLOUD = auto()
    SPOTIFY = auto()
    UNKNOWN = auto()


_PATTERNS: dict[ServiceType, re.Pattern] = {
    ServiceType.YOUTUBE: re.compile(r"(youtube\.com|youtu\.be)", re.IGNORECASE),
    ServiceType.INSTAGRAM: re.compile(r"instagram\.com", re.IGNORECASE),
    ServiceType.PINTEREST: re.compile(r"(pinterest\.com|pin\.it)", re.IGNORECASE),
    ServiceType.SOUNDCLOUD: re.compile(r"soundcloud\.com", re.IGNORECASE),
    ServiceType.SPOTIFY: re.compile(r"open\.spotify\.com", re.IGNORECASE),
}

_URL_REGEX = re.compile(r"https?://[^\s]+", re.IGNORECASE)


def extract_url(text: Optional[str]) -> Optional[str]:
    """اولین لینک http/https داخل متن را پیدا می‌کند، یا None اگر لینکی نبود."""
    if not text:
        return None
    match = _URL_REGEX.search(text)
    return match.group(0) if match else None


def detect_service(url: str) -> ServiceType:
    """با توجه به دامنه، سرویس مربوط به لینک را برمی‌گرداند."""
    for service, pattern in _PATTERNS.items():
        if pattern.search(url):
            return service
    return ServiceType.UNKNOWN
