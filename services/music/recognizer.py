"""
تشخیص آهنگ از روی فایل صوتی/ویدیویی، با استفاده از shazamio
(کتابخانه‌ای که رفتار سرویس Shazam را شبیه‌سازی می‌کند).

چرا shazamio؟
رایگان و متن‌باز است و نیازی به ثبت‌نام یا کلید API ندارد؛ جایگزین‌های رسمی
مثل ACRCloud یا AudD معمولاً پولی هستند یا پلن رایگان بسیار محدودی دارند.
"""

import logging
from pathlib import Path
from typing import Optional, TypedDict

from shazamio import Shazam

logger = logging.getLogger(__name__)


class SongInfo(TypedDict):
    title: str
    artist: str
    album: Optional[str]


async def recognize_song(file_path: Path) -> Optional[SongInfo]:
    shazam = Shazam()

    try:
        result = await shazam.recognize(str(file_path))
    except Exception:  # noqa: BLE001 - هر خطای شبکه/سرویس را می‌گیریم
        logger.exception("Shazam recognition request failed for %s", file_path)
        return None

    track = result.get("track")
    if not track:
        return None

    return SongInfo(
        title=track.get("title", "نامشخص"),
        artist=track.get("subtitle", "نامشخص"),
        album=_extract_album(track),
    )


def _extract_album(track: dict) -> Optional[str]:
    """اطلاعات آلبوم داخل ساختار تودرتوی sections پنهان است؛ این تابع آن را پیدا می‌کند."""
    for section in track.get("sections", []):
        if section.get("type") != "SONG":
            continue
        for item in section.get("metadata", []):
            if item.get("title", "").strip().lower() == "album":
                return item.get("text")
    return None
