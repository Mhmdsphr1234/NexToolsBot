"""
این فایل "مغز" تشخیص خودکار ورودی است: بر اساس نوع پیام کاربر
(لینک، عکس، PDF، فایل دیگر، وویس/صوت/ویدیو)، ابزار مناسب را صدا می‌زند.

طبق طراحی پروژه، این روتر فقط مسیریابی و مدیریت پیام‌های وضعیت
("در حال دانلود...") را انجام می‌دهد؛ منطق واقعی هر قابلیت داخل
services/ پیاده‌سازی شده و اینجا فقط صدا زده می‌شود.
"""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)

from app.config import settings
from services.downloader.base import DownloadError
from services.downloader.registry import get_downloader
from services.downloader.spotify import SpotifyDownloadError
from services.music.recognizer import recognize_song
from services.ocr.ocr_service import extract_text
from services.pdf_tools.image_to_pdf import images_to_pdf
from services.pdf_tools.pdf_to_image import pdf_to_images
from services.upload.file_host import FileHostError, upload_and_get_link
from utils.file_helpers import cleanup_files
from utils.url_detector import ServiceType, detect_service, extract_url

logger = logging.getLogger(__name__)
router = Router(name="main")

# --- حافظه موقت برای گروه‌بندی آلبوم عکس‌ها و برای دکمه‌های PDF/OCR ---
# نکته: این‌ها in-memory هستند؛ یعنی با ری‌استارت ربات پاک می‌شوند.
# برای یک ربات تک‌پردازه (که همین حالت پروژه است) این کاملاً کافی است.
_album_buffer: dict[str, list[Message]] = {}
_pending_photo_jobs: dict[str, list[Path]] = {}

ALBUM_DEBOUNCE_SECONDS = 1.5


async def _collect_album(message: Message) -> Optional[list[Message]]:
    """
    وقتی کاربر چند عکس را با هم به‌صورت آلبوم می‌فرستد، تلگرام آن‌ها را در
    چند پیام جدا (با media_group_id یکسان) تحویل می‌دهد. این تابع کمی صبر
    می‌کند تا همه‌ی پیام‌های آلبوم برسند و سپس همه را یک‌جا برمی‌گرداند.
    """
    group_id = message.media_group_id
    if group_id is None:
        return [message]

    _album_buffer.setdefault(group_id, []).append(message)
    await asyncio.sleep(ALBUM_DEBOUNCE_SECONDS)

    messages = _album_buffer.get(group_id)
    if messages is None:
        return None

    # فقط آخرین Handler که برای این گروه صدا زده شده، اجازه پردازش دارد؛
    # بقیه (که زودتر رسیدند) کاری انجام نمی‌دهند تا آلبوم دوبار پردازش نشود.
    if messages[-1].message_id != message.message_id:
        return None

    del _album_buffer[group_id]
    return messages


# ---------------------------------------------------------------------------
# ۱. پیام متنی حاوی لینک -> دانلودر مناسب
# ---------------------------------------------------------------------------
@router.message(F.text)
async def handle_text(message: Message) -> None:
    url = extract_url(message.text)
    if not url:
        await message.answer(
            "متوجه نشدم چی می‌خوای! 🤔\n"
            "یه لینک (یوتیوب/اینستاگرام/پینترست/ساندکلاود/اسپاتیفای)، عکس، "
            "PDF، وویس یا فایل صوتی/ویدیویی برام بفرست."
        )
        return

    service = detect_service(url)
    downloader = get_downloader(service)

    if downloader is None:
        await message.answer(
            "⚠️ این لینک رو فعلاً پشتیبانی نمی‌کنم.\n"
            "فعلاً یوتیوب، اینستاگرام، پینترست، ساندکلاود و اسپاتیفای پشتیبانی می‌شن."
        )
        return

    status_msg = await message.answer("⬇️ در حال دانلود...")
    try:
        file_path = await downloader(url)

        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > settings.max_file_size_mb:
            await status_msg.edit_text(
                f"⚠️ فایل دانلود شد ولی حجمش ({size_mb:.1f} مگابایت) بیشتر از حد "
                f"مجاز ({settings.max_file_size_mb} مگابایت) برای ارسال در تلگرامه."
            )
        else:
            await status_msg.edit_text("✅ دانلود کامل شد. در حال ارسال...")
            await _send_downloaded_file(message, file_path, service)

        cleanup_files([file_path])

    except (DownloadError, SpotifyDownloadError) as exc:
        await status_msg.edit_text(f"⚠️ {exc}")
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error while handling url=%s", url)
        await status_msg.edit_text("⚠️ یه خطای غیرمنتظره پیش اومد. لطفاً دوباره امتحان کن.")


async def _send_downloaded_file(message: Message, file_path: Path, service: ServiceType) -> None:
    """بر اساس نوع فایل، آن را به فرمت مناسب (ویدیو/صوت/فایل) در تلگرام ارسال می‌کند."""
    suffix = file_path.suffix.lower()
    input_file = FSInputFile(file_path)

    if suffix in (".mp4", ".mov", ".webm", ".mkv"):
        await message.answer_video(input_file, caption="🎬 دانلود شما")
    elif suffix in (".mp3", ".m4a", ".ogg", ".opus", ".wav"):
        await message.answer_audio(input_file, caption="🎵 دانلود شما")
    else:
        await message.answer_document(input_file, caption="📁 دانلود شما")


# ---------------------------------------------------------------------------
# ۲. عکس -> بعد از دریافت، دو دکمه: تبدیل به PDF یا استخراج متن (OCR)
# ---------------------------------------------------------------------------
@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot) -> None:
    try:
        messages = await _collect_album(message)
        if messages is None:
            return  # بقیه‌ی پیام‌های همین آلبوم قبلاً در حال پردازش هستند

        settings.download_dir.mkdir(exist_ok=True)
        image_paths: list[Path] = []
        for msg in messages:
            photo = msg.photo[-1]  # بزرگ‌ترین سایز موجود از عکس
            destination = settings.download_dir / f"{uuid.uuid4().hex}.jpg"
            await bot.download(photo, destination=destination)
            image_paths.append(destination)

        token = uuid.uuid4().hex
        _pending_photo_jobs[token] = image_paths

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📄 تبدیل به PDF", callback_data=f"topdf:{token}"),
                    InlineKeyboardButton(text="🔤 استخراج متن (OCR)", callback_data=f"ocr:{token}"),
                ]
            ]
        )

        count_text = f"{len(image_paths)} عکس" if len(image_paths) > 1 else "عکس"
        await message.answer(f"{count_text} دریافت شد! چیکار کنم؟", reply_markup=keyboard)

    except Exception:  # noqa: BLE001
        logger.exception("Failed to receive photo(s)")
        await message.answer("⚠️ دریافت عکس با خطا مواجه شد. لطفاً دوباره امتحان کن.")


@router.callback_query(F.data.startswith("topdf:"))
async def callback_to_pdf(callback: CallbackQuery) -> None:
    token = callback.data.split(":", 1)[1]
    image_paths = _pending_photo_jobs.pop(token, None)

    if image_paths is None:
        await callback.answer("این درخواست منقضی شده، لطفاً دوباره عکس رو بفرست.", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text("📄 در حال تبدیل به PDF...")

    try:
        pdf_path = images_to_pdf(image_paths)
        await callback.message.answer_document(FSInputFile(pdf_path), caption="فایل PDF شما 📄")
        cleanup_files(image_paths + [pdf_path])
    except Exception:  # noqa: BLE001
        logger.exception("Failed to convert photos to PDF")
        await callback.message.answer("⚠️ تبدیل به PDF با خطا مواجه شد.")
        cleanup_files(image_paths)


@router.callback_query(F.data.startswith("ocr:"))
async def callback_ocr(callback: CallbackQuery) -> None:
    token = callback.data.split(":", 1)[1]
    image_paths = _pending_photo_jobs.pop(token, None)

    if image_paths is None:
        await callback.answer("این درخواست منقضی شده، لطفاً دوباره عکس رو بفرست.", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text("🔤 در حال استخراج متن...")

    try:
        # برای سادگی MVP، OCR فقط روی اولین عکس اجرا می‌شود (اگر چند عکس فرستاده شده باشد)
        text = extract_text(image_paths[0])
        if not text:
            await callback.message.edit_text("😕 متنی داخل این عکس پیدا نشد.")
        else:
            await callback.message.edit_text(f"متن استخراج‌شده:\n\n{text}")
        cleanup_files(image_paths)
    except Exception:  # noqa: BLE001
        logger.exception("OCR failed")
        await callback.message.edit_text("⚠️ استخراج متن با خطا مواجه شد.")
        cleanup_files(image_paths)


# ---------------------------------------------------------------------------
# ۳. فایل PDF -> تبدیل به عکس  |  هر فایل دیگر -> ساخت لینک دانلود
# ---------------------------------------------------------------------------
@router.message(F.document)
async def handle_document(message: Message, bot: Bot) -> None:
    document = message.document
    try:
        if document.mime_type == "application/pdf":
            await _handle_pdf_to_images(message, bot)
        else:
            await _handle_file_to_link(message, bot)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to process document")
        await message.answer("⚠️ پردازش این فایل با خطا مواجه شد. لطفاً دوباره امتحان کن.")


async def _handle_pdf_to_images(message: Message, bot: Bot) -> None:
    status_msg = await message.answer("📄 در حال تبدیل PDF به عکس...")

    settings.download_dir.mkdir(exist_ok=True)
    pdf_path = settings.download_dir / f"{uuid.uuid4().hex}.pdf"
    await bot.download(message.document, destination=pdf_path)

    image_paths = pdf_to_images(pdf_path)

    await status_msg.edit_text(f"✅ {len(image_paths)} صفحه پیدا شد. در حال ارسال...")

    # تلگرام حداکثر ۱۰ آیتم را در یک آلبوم (media group) قبول می‌کند
    media_items = [InputMediaPhoto(media=FSInputFile(p)) for p in image_paths]
    for i in range(0, len(media_items), 10):
        chunk = media_items[i : i + 10]
        if len(chunk) == 1:
            await message.answer_photo(chunk[0].media)
        else:
            await message.answer_media_group(chunk)

    cleanup_files(image_paths + [pdf_path])


async def _handle_file_to_link(message: Message, bot: Bot) -> None:
    document = message.document
    max_bytes = settings.max_file_size_mb * 1024 * 1024

    if document.file_size and document.file_size > max_bytes:
        await message.answer(
            f"⚠️ حجم این فایل بیشتر از {settings.max_file_size_mb} مگابایت مجازه."
        )
        return

    status_msg = await message.answer("📁 در حال آپلود فایل و ساخت لینک دانلود...")

    settings.download_dir.mkdir(exist_ok=True)
    safe_name = document.file_name or "file"
    file_path = settings.download_dir / f"{uuid.uuid4().hex}_{safe_name}"
    await bot.download(document, destination=file_path)

    try:
        link = await upload_and_get_link(file_path)
        await status_msg.edit_text(f"✅ لینک دانلود فایل شما:\n{link}")
    except FileHostError as exc:
        await status_msg.edit_text(f"⚠️ {exc}")
    finally:
        cleanup_files([file_path])


# ---------------------------------------------------------------------------
# ۴. وویس / فایل صوتی / ویدیو -> تشخیص آهنگ
# ---------------------------------------------------------------------------
@router.message(F.voice | F.audio | F.video)
async def handle_media_for_recognition(message: Message, bot: Bot) -> None:
    status_msg = await message.answer("🎧 در حال گوش دادن و تشخیص آهنگ...")

    try:
        media = message.voice or message.audio or message.video
        if message.voice:
            ext = "ogg"
        elif message.video:
            ext = "mp4"
        else:
            ext = "mp3"

        settings.download_dir.mkdir(exist_ok=True)
        file_path = settings.download_dir / f"{uuid.uuid4().hex}.{ext}"
        await bot.download(media, destination=file_path)

        result = await recognize_song(file_path)

        if result is None:
            await status_msg.edit_text("😕 نتونستم آهنگ رو تشخیص بدم. شاید کیفیت صدا کافی نبوده.")
        else:
            text = f"🎵 آهنگ: {result['title']}\n🎤 خواننده: {result['artist']}"
            if result.get("album"):
                text += f"\n💿 آلبوم: {result['album']}"
            await status_msg.edit_text(text)

        cleanup_files([file_path])

    except Exception:  # noqa: BLE001
        logger.exception("Song recognition failed")
        await status_msg.edit_text("⚠️ تشخیص آهنگ با خطا مواجه شد. لطفاً دوباره امتحان کن.")
