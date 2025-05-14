import logging
import requests
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)
from deep_translator import GoogleTranslator

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

API_WEATHER = "3ecd72d6-71c7-423b-a4e9-8f0e28001fc5"
TOKEN = "7917742805:AAFaZFgyFkSQIlkm-n6PC3D577LwTYYuQT0"
DEFAULT_TARGET_LANG = "ru"


class TranslationBot:
    def __init__(self):
        self.target_lang = DEFAULT_TARGET_LANG
        self.translator = GoogleTranslator(source='auto', target=DEFAULT_TARGET_LANG)

    async def start(self, update, context):
        user = update.effective_user
        await update.message.reply_text(
            f"👋 Привет, {user.first_name}!\n"
            f"Я бот-переводчик. Сейчас перевожу на {self.target_lang}.\n\n"
            "Просто отправь мне текст для перевода.\n"
            "Команды:\n"
            "/lang <код> - сменить язык перевода (например /lang en)\n"
            "/weather <город> - узнать погоду\n"
            "/help - справка"
        )

    async def help_command(self, update, context):
        await update.message.reply_text(
            "ℹ️ Справка:\n"
            "Отправьте текст для автоматического перевода\n\n"
            "Команды:\n"
            "/lang <код> - изменить язык перевода\n"
            "/weather <город> - узнать погоду\n"
            "/current - текущие настройки\n"
            "/help - эта справка"
        )

    async def set_language(self, update, context):
        if not context.args:
            await update.message.reply_text("❌ Укажите код языка (например /lang en)")
            return

        self.target_lang = context.args[0].lower()
        self.translator.target = self.target_lang
        await update.message.reply_text(f"✅ Язык перевода изменен на: {self.target_lang}")

    async def show_settings(self, update, context):
        await update.message.reply_text(
            f"⚙️ Текущие настройки:\n"
            f"Язык перевода: {self.target_lang}"
        )

    async def translate_text(self, update, context):
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

    async def get_weather_by_city(self, update, context):
        if not context.args:
            await update.message.reply_text("❌ Укажите город, например: /weather Москва")
            return

        city_name = ' '.join(context.args)

        try:
            # 1. Геокодирование: получаем координаты города
            geocode_url = "https://geocode-maps.yandex.ru/1.x/"
            geocode_params = {
                "apikey": '8013b162-6b42-4997-9691-77b7074026e0',
                "format": "json",
                "geocode": city_name,
                "results": 1,
            }

            geo_response = requests.get(geocode_url, params=geocode_params)
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            # Проверяем, найден ли город
            features = geo_data["response"]["GeoObjectCollection"]["featureMember"]
            if not features:
                await update.message.reply_text("❌ Город не найден. Проверьте название.")
                return

            # Извлекаем координаты
            pos = features[0]["GeoObject"]["Point"]["pos"]
            lon, lat = pos.split()  # Долгота и широта

            # 2. Запрос погоды по координатам
            weather_url = "https://api.weather.yandex.ru/v2/forecast"
            weather_params = {
                "lat": lat,
                "lon": lon,
                "lang": "ru_RU",
                "limit": 1,
            }
            weather_headers = {"X-Yandex-API-Key": API_WEATHER}

            weather_response = requests.get(
                weather_url,
                params=weather_params,
                headers=weather_headers,
            )
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            # 3. Форматируем ответ
            fact = weather_data["fact"]

            # Словарь для перевода погодных условий
            conditions = {
                "clear": "ясно ☀️",
                "partly-cloudy": "малооблачно 🌤",
                "cloudy": "облачно ☁️",
                "overcast": "пасмурно 🌫",
                "rain": "дождь 🌧",
                "thunderstorm": "гроза ⚡️",
                "snow": "снег ❄️",
            }

            weather_condition = conditions.get(fact["condition"], fact["condition"])

            weather_message = (
                f"🌦 Погода в {city_name}:\n"
                f"• Температура: {fact['temp']}°C (ощущается как {fact['feels_like']}°C)\n"
                f"• Погода: {weather_condition}\n"
                f"• Ветер: {fact['wind_speed']} м/с, {fact['wind_dir']}\n"
                f"• Давление: {fact['pressure_mm']} мм рт. ст.\n"
                f"• Влажность: {fact['humidity']}%"
            )

            await update.message.reply_text(weather_message)

        except Exception as e:
            logger.error(f"Weather API error: {e}")
            await update.message.reply_text("❌ Ошибка при запросе погоды. Попробуйте позже.")

def main():
    bot = TranslationBot()

    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("help", bot.help_command))
    app.add_handler(CommandHandler("lang", bot.set_language))
    app.add_handler(CommandHandler("current", bot.show_settings))
    app.add_handler(CommandHandler("weather", bot.get_weather_by_city))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.translate_text))

    logger.info("Бот работает!")
    app.run_polling()


if __name__ == '__main__':
    main()