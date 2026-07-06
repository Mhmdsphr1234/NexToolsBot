from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router(name="start")

WELCOME_TEXT = (
    "سلام! 👋\n"
    "به <b>NexTools</b> خوش اومدی.\n\n"
    "کافیه یکی از موارد زیر رو برام بفرستی، خودم تشخیص می‌دم چیکار باید بکنم:\n\n"
    "🔗 لینک یوتیوب / اینستاگرام / پینترست / ساندکلاود / اسپاتیفای → دانلود می‌کنم\n"
    "🖼 عکس → تبدیل به PDF یا استخراج متن (OCR)\n"
    "📄 فایل PDF → تبدیل به عکس\n"
    "🎙 وویس، فایل صوتی یا ویدیو → تشخیص آهنگ\n"
    "📁 هر فایل دیگه‌ای → یه لینک دانلود مستقیم برات می‌سازم\n\n"
    "برای دیدن دوباره این راهنما، /help رو بفرست."
)


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT)


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    await message.answer(WELCOME_TEXT)
