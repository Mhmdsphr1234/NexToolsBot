"""
منطق مشترک دانلود از طریق yt-dlp.

چرا یک فایل مشترک؟
یوتیوب، اینستاگرام، پینترست و ساندکلاود همگی توسط yt-dlp پشتیبانی می‌شوند؛
پس منطق دانلود یکی است و فقط تنظیمات جزئی (extra_opts) فرق می‌کند.
این از تکرار کد در چهار فایل جلوگیری می‌کند.

نکته فنی مهم: yt-dlp یک کتابخانه synchronous (غیر async) است.
اگر مستقیم صدا زده شود، کل ربات را برای همه کاربران دیگر قفل می‌کند.
به همین دلیل، اجرای آن را به یک Thread جداگانه می‌سپاریم
(loop.run_in_executor) تا حلقه اصلی asyncio آزاد بماند.
"""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any, Optional

import yt_dlp

from app.config import settings

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """هر خطای مربوط به دانلود، با یک پیام قابل‌فهم برای کاربر."""


def _run_ytdlp(url: str, output_template: str, extra_opts: Optional[dict[str, Any]]) -> Path:
    opts: dict[str, Any] = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "restrictfilenames": True,
        "retries": 3,
    }
    if extra_opts:
        opts.update(extra_opts)

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        # اگر postprocessor فرمت فایل را عوض کرده باشد (مثلاً تبدیل به mp3)،
        # پسوند فایل نهایی با آنچه yt-dlp حدس می‌زند فرق دارد؛ اینجا هر دو حالت را چک می‌کنیم.
        final_path = Path(filename)
        if not final_path.exists() and extra_opts and "postprocessors" in extra_opts:
            for pp in extra_opts["postprocessors"]:
                new_ext = pp.get("preferredcodec")
                if new_ext:
                    candidate = final_path.with_suffix(f".{new_ext}")
                    if candidate.exists():
                        final_path = candidate
                        break

        return final_path


async def download_with_ytdlp(
    url: str,
    extra_opts: Optional[dict[str, Any]] = None,
) -> Path:
    """
    یک لینک را با yt-dlp دانلود می‌کند و مسیر فایل نهایی را برمی‌گرداند.
    در صورت بروز هر خطا، DownloadError با پیام قابل نمایش به کاربر raise می‌شود.
    """
    settings.download_dir.mkdir(exist_ok=True)

    # uuid در نام فایل تا در صورت دانلود همزمان چند کاربر، فایل‌ها با هم تداخل نکنند.
    unique_name = f"{uuid.uuid4().hex}_%(title).50s.%(ext)s"
    output_template = str(settings.download_dir / unique_name)

    loop = asyncio.get_running_loop()
    try:
        file_path = await loop.run_in_executor(
            None, _run_ytdlp, url, output_template, extra_opts
        )
    except Exception as exc:  # noqa: BLE001 - می‌خواهیم هر نوع خطای yt-dlp را بگیریم
        logger.exception("yt-dlp failed for url=%s", url)
        raise DownloadError(
            "دانلود این لینک ممکن نشد. ممکن است لینک خصوصی، حذف‌شده یا نامعتبر باشد."
        ) from exc

    if not file_path.exists():
        raise DownloadError("فایل دانلود شد ولی روی دیسک پیدا نشد؛ لطفاً دوباره تلاش کن.")

    return file_path
