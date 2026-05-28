import asyncio
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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

PROCESSING_MESSAGE = "⏳ Обрабатываю ваш запрос, это может занять некоторое время..."

executor = ThreadPoolExecutor(max_workers=4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Привет! Я мультиагентный бот.\n\n"
        "У меня есть команда специалистов:\n"
        "🧠 *Оркестратор* — анализирует задачи и координирует команду\n"
        "💻 *Программист* — решает технические задачи и пишет код\n"
        "✍️ *Копирайтер* — создаёт тексты и контент\n"
        "🎨 *Дизайнер* — даёт советы по дизайну и визуалу\n\n"
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
        "Просто напишите любое сообщение — бот автоматически определит тип задачи "
        "и подключит нужного специалиста.\n\n"
        "*Примеры запросов:*\n"
        "• Напиши функцию на Python для сортировки списка\n"
        "• Придумай слоган для кофейни\n"
        "• Посоветуй цветовую палитру для мобильного приложения\n"
        "• Объясни, как работает рекурсия\n\n"
        "Бот помнит контекст последних 10 сообщений. "
        "Используйте /clear чтобы начать новый диалог.",
        parse_mode="Markdown",
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    clear_history(user_id)
    await update.message.reply_text(
        "🗑 История диалога очищена. Начинаем с чистого листа!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_message = update.message.text

    count = history_size(user_id)
    context_note = f" (в памяти: {count} сообщ.)" if count > 0 else ""
    processing_msg = await update.message.reply_text(
        PROCESSING_MESSAGE + context_note
    )

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor, run_crew, user_message, user_id
        )
        await processing_msg.delete()

        max_length = 4096
        if len(result) <= max_length:
            await update.message.reply_text(result)
        else:
            chunks = [result[i:i + max_length] for i in range(0, len(result), max_length)]
            for chunk in chunks:
                await update.message.reply_text(chunk)

    except Exception as e:
        logger.error("Error processing message: %s", e, exc_info=True)
        await processing_msg.edit_text(
            "❌ Произошла ошибка при обработке запроса. Пожалуйста, попробуйте ещё раз."
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
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.add_error_handler(error_handler)

    logger.info("Bot started, polling for updates...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        close_loop=False,
    )


if __name__ == "__main__":
    main()
