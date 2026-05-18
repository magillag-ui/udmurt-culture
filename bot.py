import asyncio
import uuid
import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from supabase import create_client, Client

# ====== НАСТРОЙКИ ======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
SUPABASE_URL = "https://wvefhluawpggyesscajs.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind2ZWZobHVhd3BnZ3llc3NjYWpzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg5NDI3MjMsImV4cCI6MjA5NDUxODcyM30.0wQ-Alvfj-gcASjhtkt7vCmy1o-66N6uwu7DvGTBFug"
# =======================

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я готов сохранять культуру Удмуртии. 🏔️\n\n"
        "Просто пришли мне фото, видео или аудио,\n"
        "связанное с культурой Удмуртии - и я сохраню его в нашу коллекцию!\n\n"
        "Можешь добавить описание к файлу в подписи."
    )


async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    await message.reply_text("⏳ Получаю файл, подожди немного...")

    # Определяем тип файла
    if message.photo:
        file = await message.photo[-1].get_file()
        file_type = "photo"
        ext = "jpg"
        content_type = "image/jpeg"
    elif message.video:
        file = await message.video.get_file()
        file_type = "video"
        ext = "mp4"
        content_type = "video/mp4"
    elif message.audio:
        file = await message.audio.get_file()
        file_type = "audio"
        ext = "mp3"
        content_type = "audio/mpeg"
    elif message.voice:
        file = await message.voice.get_file()
        file_type = "audio"
        ext = "ogg"
        content_type = "audio/ogg"
    else:
        await message.reply_text("Пожалуйста, отправь фото, видео или аудио файл.")
        return

    try:
        # Скачиваем файл
        file_bytes = await file.download_as_bytearray()
        filename = f"{uuid.uuid4()}.{ext}"

        # Загружаем в Supabase Storage
        supabase.storage.from_("files").upload(
            filename,
            bytes(file_bytes),
            {"content-type": content_type}
        )

        # Получаем публичную ссылку
        file_url = supabase.storage.from_("files").get_public_url(filename)

        # Описание из подписи к файлу
        description = message.caption or ""

        # Сохраняем в базу данных
        supabase.table("materials").insert({
            "file_url": file_url,
            "file_type": file_type,
            "description": description,
            "status": "pending",
            "original_filename": filename
        }).execute()

        await message.reply_text(
            "✅ Файл получен и отправлен на проверку!\n\n"
            "После одобрения он появится на сайте и в программе.\n"
            "Спасибо за вклад в сохранение культуры Удмуртии! 🙏"
        )

    except Exception as e:
        await message.reply_text("❌ Произошла ошибка при загрузке. Попробуй ещё раз.")
        print(f"Ошибка: {e}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пришли мне фото, видео или аудио файл,\n"
        "связанный с культурой Удмуртии! 📸🎬🎵"
    )


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE,
        handle_media
    ))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("✅ Бот запущен! Нажми Ctrl+C чтобы остановить.")
    app.run_polling()


if __name__ == "__main__":
    main()
