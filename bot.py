import asyncio
import base64
import io
import logging
from concurrent.futures import ThreadPoolExecutor
from telegram import Update
from telegram.error import Conflict, NetworkError
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from config import TELEGRAM_TOKEN
from crew_manager import run_crew
from history import clear_history, history_size
from agents import IMAGE_URL_PREFIX, IMAGE_B64_PREFIX
from doc_extractor import extract_text, is_supported

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

PROCESSING_MESSAGE = "⏳ Обрабатываю ваш запрос, это может занять некоторое время..."
PROCESSING_IMAGE_MESSAGE = "🖼 Анализирую изображение, это может занять некоторое время..."
GENERATING_IMAGE_MESSAGE = "🎨 Генерирую изображение с помощью gpt-image-1..."
PROCESSING_DOCUMENT_MESSAGE = "📄 Извлекаю текст из документа и анализирую..."

executor = ThreadPoolExecutor(max_workers=4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Привет! Я мультиагентный бот.\n\n"
        "У меня есть команда специалистов:\n"
        "🧠 *Оркестратор* — анализирует задачи и координирует команду\n"
        "💻 *Программист* — решает технические задачи и пишет код\n"
        "✍️ *Копирайтер* — создаёт тексты и контент\n"
        "🎨 *Дизайнер* — даёт советы по дизайну и генерирует изображения\n\n"
        "Я умею:\n"
        "• Отвечать на текстовые вопросы\n"
        "• 🖼 Анализировать фотографии (описание, OCR, дизайн-ревью)\n"
        "• 🎨 Генерировать изображения по описанию\n"
        "• 📄 Читать и анализировать документы (PDF, TXT, DOCX)\n\n"
        "Я помню последние 10 сообщений нашего диалога.\n\n"
        "Команды:\n"
        "/start — это сообщение\n"
        "/help — примеры запросов\n"
        "/clear — очистить историю диалога",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ℹ️ *Как использовать бота:*\n\n"
        "Просто напишите любое сообщение или пришлите фото.\n\n"
        "*Текстовые запросы:*\n"
        "• Напиши функцию на Python для сортировки\n"
        "• Придумай слоган для кофейни\n"
        "• Посоветуй цветовую палитру для приложения\n\n"
        "*Генерация изображений:*\n"
        "• Нарисуй закат над горами в стиле аниме\n"
        "• Сгенерируй картинку с котом-астронавтом\n"
        "• Создай изображение современного офиса\n\n"
        "*Анализ фотографий:*\n"
        "• Пришли фото — бот опишет, что на нём\n"
        "• Скриншот кода → анализ ошибок\n"
        "• Скриншот интерфейса → дизайн-ревью\n"
        "• Фото документа → извлечение текста\n\n"
        "*Работа с документами:*\n"
        "• Пришли PDF/TXT/DOCX — бот прочитает и ответит на вопросы\n"
        "• С подписью: «Выдели ключевые тезисы» или «Сделай краткое резюме»\n"
        "• Без подписи — бот сделает общее резюме документа\n\n"
        "Используйте /clear чтобы начать новый диалог.",
        parse_mode="Markdown",
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    clear_history(user_id)
    await update.message.reply_text(
        "🗑 История диалога очищена. Начинаем с чистого листа!"
    )


async def _send_result(update: Update, result: str) -> None:
    if result.startswith(IMAGE_URL_PREFIX):
        url = result[len(IMAGE_URL_PREFIX):]
        await update.message.reply_photo(
            photo=url,
            caption="🎨 Изображение сгенерировано",
        )
        return

    if result.startswith(IMAGE_B64_PREFIX):
        b64_data = result[len(IMAGE_B64_PREFIX):]
        image_bytes = base64.b64decode(b64_data)
        await update.message.reply_photo(
            photo=io.BytesIO(image_bytes),
            caption="🎨 Изображение сгенерировано с помощью gpt-image-1",
        )
        return

    max_length = 4096
    if len(result) <= max_length:
        await update.message.reply_text(result)
    else:
        chunks = [result[i:i + max_length] for i in range(0, len(result), max_length)]
        for chunk in chunks:
            await update.message.reply_text(chunk)


def _is_image_gen(message: str) -> bool:
    from crew_manager import is_image_generation_request
    return is_image_generation_request(message)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_message = update.message.text

    if _is_image_gen(user_message):
        processing_msg = await update.message.reply_text(GENERATING_IMAGE_MESSAGE)
    else:
        count = history_size(user_id)
        context_note = f" (в памяти: {count} сообщ.)" if count > 0 else ""
        processing_msg = await update.message.reply_text(PROCESSING_MESSAGE + context_note)

    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(executor, run_crew, user_message, user_id)
        await processing_msg.delete()
        await _send_result(update, result)

    except Exception as e:
        logger.error("Error processing message: %s", e, exc_info=True)
        await processing_msg.edit_text(
            "❌ Произошла ошибка при обработке запроса. Пожалуйста, попробуйте ещё раз."
        )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    caption = update.message.caption or "Проанализируй изображение"

    count = history_size(user_id)
    context_note = f" (в памяти: {count} сообщ.)" if count > 0 else ""
    processing_msg = await update.message.reply_text(
        PROCESSING_IMAGE_MESSAGE + context_note
    )

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        byte_array = await file.download_as_bytearray()
        image_b64 = base64.b64encode(bytes(byte_array)).decode("utf-8")

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            executor, run_crew, caption, user_id, image_b64, "image/jpeg"
        )
        await processing_msg.delete()
        await _send_result(update, result)

    except Exception as e:
        logger.error("Error processing photo: %s", e, exc_info=True)
        await processing_msg.edit_text(
            "❌ Не удалось обработать изображение. Пожалуйста, попробуйте ещё раз."
        )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    doc = update.message.document
    caption = update.message.caption or "Сделай подробное резюме этого документа"

    mime_type = doc.mime_type
    file_name = doc.file_name or ""

    if not is_supported(mime_type, file_name):
        await update.message.reply_text(
            "⚠️ Формат не поддерживается. Я работаю с PDF, TXT и DOCX файлами."
        )
        return

    processing_msg = await update.message.reply_text(PROCESSING_DOCUMENT_MESSAGE)

    try:
        file = await context.bot.get_file(doc.file_id)
        byte_array = await file.download_as_bytearray()
        file_bytes = bytes(byte_array)

        extracted = extract_text(file_bytes, mime_type, file_name)
        if not extracted.strip():
            await processing_msg.edit_text(
                "⚠️ Не удалось извлечь текст из документа. "
                "Возможно, PDF содержит только сканы без OCR."
            )
            return

        char_count = len(extracted)
        full_message = (
            f"{caption}\n\n"
            f"--- СОДЕРЖИМОЕ ДОКУМЕНТА ({file_name}, ~{char_count} симв.) ---\n\n"
            f"{extracted}"
        )

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(executor, run_crew, full_message, user_id)
        await processing_msg.delete()
        await _send_result(update, result)

    except Exception as e:
        logger.error("Error processing document: %s", e, exc_info=True)
        await processing_msg.edit_text(
            f"❌ Не удалось обработать документ: {e}"
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if isinstance(context.error, Conflict):
        logger.warning("Conflict error — another instance may be running. Retrying in 5s...")
        await asyncio.sleep(5)
    elif isinstance(context.error, NetworkError):
        logger.warning("Network error: %s. Will retry automatically.", context.error)
    else:
        logger.error("Unhandled error: %s", context.error, exc_info=context.error)


def main() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.add_error_handler(error_handler)

    logger.info("Bot started with image generation and understanding support, polling for updates...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
