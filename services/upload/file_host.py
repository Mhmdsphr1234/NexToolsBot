"""
آپلود فایل و ساخت لینک دانلود مستقیم.

چرا 0x0.st؟
برای MVP، هدف رسیدن سریع به یک نسخه قابل‌اجراست. 0x0.st یک سرویس رایگان و
بدون نیاز به حساب کاربری است که با یک درخواست POST ساده فایل را آپلود و
یک لینک برمی‌گرداند (فایل‌ها حداقل ۳۰ روز نگه داشته می‌شوند).

⚠️ محدودیت مهم: این سرویس عمومی و موقتی است، مناسب مرحله MVP.
برای نسخه‌های تولیدی/حرفه‌ای‌تر (Phase 2 به بعد طبق Roadmap)، پیشنهاد می‌شود
به یک سرویس ذخیره‌سازی اختصاصی (مثل MinIO یا S3-compatible storage روی VPS خودتان)
مهاجرت شود؛ چون در آنجا کنترل کامل روی نگهداری، امنیت و مدت‌زمان فایل‌ها دارید.
"""

from pathlib import Path

import aiohttp

_UPLOAD_URL = "https://0x0.st"
_HEADERS = {"User-Agent": "NexToolsTelegramBot/1.0"}


class FileHostError(Exception):
    """خطای مربوط به آپلود فایل و ساخت لینک."""


async def upload_and_get_link(file_path: Path) -> str:
    try:
        async with aiohttp.ClientSession(headers=_HEADERS) as session:
            with open(file_path, "rb") as file_obj:
                form = aiohttp.FormData()
                form.add_field("file", file_obj, filename=file_path.name)

                async with session.post(_UPLOAD_URL, data=form) as response:
                    if response.status != 200:
                        raise FileHostError(
                            f"سرویس آپلود خطا برگرداند (کد {response.status})."
                        )
                    link = (await response.text()).strip()
                    return link
    except aiohttp.ClientError as exc:
        raise FileHostError(f"اتصال به سرویس آپلود ناموفق بود: {exc}") from exc
