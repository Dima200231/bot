import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from deep_translator import GoogleTranslator

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "7917742805:AAFaZFgyFkSQIlkm-n6PC3D577LwTYYuQT0"
DEFAULT_TARGET_LANG = "ru"


class TranslationBot:
    def __init__(self):
        self.target_lang = DEFAULT_TARGET_LANG
        self.translator = GoogleTranslator(source='auto', target=DEFAULT_TARGET_LANG)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        await update.message.reply_text(
            f"👋 Привет, {user.first_name}!\n"
            f"Я бот-переводчик. Сейчас перевожу на {self.target_lang}.\n\n"
            "Просто отправь мне текст для перевода.\n"
            "Команды:\n"
            "/lang <код> - сменить язык перевода (например /lang en)\n"
            "/help - справка"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "ℹ️ Справка:\n"
            "Отправьте текст для автоматического перевода\n\n"
            "Команды:\n"
            "/lang <код> - изменить язык перевода\n"
            "/current - текущие настройки\n"
            "/help - эта справка"
        )

    async def set_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.message.reply_text("❌ Укажите код языка (например /lang en)")
            return

        self.target_lang = context.args[0].lower()
        self.translator.target = self.target_lang
        await update.message.reply_text(f"✅ Язык перевода изменен на: {self.target_lang}")

    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            f"⚙️ Текущие настройки:\n"
            f"Язык перевода: {self.target_lang}"
        )

    async def translate_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        text = update.message.text.strip()

        if not text:
            await update.message.reply_text("❌ Вы отправили пустое сообщение")
            return

        try:
            translation = self.translator.translate(text)
            await update.message.reply_text(f"🔤 Перевод:\n{translation}")
        except Exception as e:
            logger.error(f"Translation error: {e}")
            await update.message.reply_text("❌ Ошибка перевода. Попробуйте позже.")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error("Exception:", exc_info=context.error)
        if isinstance(update, Update) and update.message:
            await update.message.reply_text("⚠️ Произошла ошибка. Попробуйте снова.")


def main():
    bot = TranslationBot()

    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("help", bot.help_command))
    app.add_handler(CommandHandler("lang", bot.set_language))
    app.add_handler(CommandHandler("current", bot.show_settings))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.translate_text))

    # Обработчик ошибок
    app.add_error_handler(bot.error_handler)

    logger.info("Бот запущен...")
    app.run_polling()


if __name__ == '__main__':
    main()