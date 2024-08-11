import logging
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import random
import datetime
import os
from gtts import gTTS
import speech_recognition as sr

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class TextAssistant:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.assistant_active = True
        self.mode = "text"
        self.language = "uk"
        self.custom_commands = {}
        self.user_data = {}
        self.admin_password = "Admin12"
        self.messages_file = "Message.txt"

        self.bot = telegram.Bot(token=self.bot_token)
        self.application = Application.builder().token(self.bot_token).build()

        # Завантаження команд і модів
        self.load_custom_commands()
        self.mods = []
        self.load_mods()

        # Додавання базових обробників команд
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("settings", self.settings))
        self.application.add_handler(CommandHandler("log", self.admin_menu))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_command))
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice_command))
        self.application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.AUDIO, self.handle_media))
        self.application.add_handler(MessageHandler(filters.TEXT, self.handle_emoji))
        self.application.add_handler(CallbackQueryHandler(self.button))

    def load_custom_commands(self):
        try:
            with open("custom_commands.txt", "r", encoding="utf-8") as file:
                for line in file:
                    if "--" in line:
                        command, response = line.strip().split("--", 1)
                        self.custom_commands[command.strip()] = response.strip()
        except FileNotFoundError:
            pass

    def save_custom_commands(self):
        try:
            with open("custom_commands.txt", "w", encoding="utf-8") as file:
                for command, response in self.custom_commands.items():
                    file.write(f"{command} -- {response}\n")
        except Exception as e:
            logger.error(f"Помилка при збереженні команд: {e}")

    def load_mods(self):
        mods_directory = 'mods'
        if os.path.exists(mods_directory):
            for filename in os.listdir(mods_directory):
                if filename.endswith('.py'):
                    mod_name = filename[:-3]
                    try:
                        mod = __import__(f'mods.{mod_name}', fromlist=[mod_name])
                        self.mods.append(mod)
                    except Exception as e:
                        logger.error(f"Помилка при завантаженні модуля '{mod_name}': {e}")
        else:
            logger.warning(f"Папка '{mods_directory}' не знайдена.")

    def log_message(self, message):
        with open(self.messages_file, "a", encoding="utf-8") as file:
            file.write(message + "\n")

    async def handle_text_command(self, update, context):
        text = update.message.text.lower()
        self.log_message(f"User: {text}")
        response = self.generate_response(text)
        if self.mode == "voice":
            await self.send_voice_response(update, response)
        else:
            await update.message.reply_text(response)
        self.log_message(f"Bot: {response}")

    async def handle_voice_command(self, update, context):
        file = await update.message.voice.get_file()
        file.download('voice_message.ogg')

        recognizer = sr.Recognizer()
        with sr.AudioFile('voice_message.ogg') as source:
            audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio, language=self.language)
            response = self.generate_response(text.lower())
            if self.mode == "voice":
                await self.send_voice_response(update, response)
            else:
                await update.message.reply_text(response)
            self.log_message(f"User (Voice): {text}")
            self.log_message(f"Bot: {response}")
        except sr.UnknownValueError:
            response = "Не вдалося розпізнати голосове повідомлення." if self.language == "uk" else "Could not understand the voice message."
            await update.message.reply_text(response)
            self.log_message(f"User (Voice): {text}")
            self.log_message(f"Bot: {response}")
        os.remove('voice_message.ogg')

    async def handle_media(self, update, context):
        await update.message.reply_text("Медіа-файли не підтримуються.")

    async def handle_emoji(self, update, context):
        text = update.message.text
        emoji_responses = {
            "😂": "Смішно, правда?",
            "😭": "О, це сумно.",
            "😍": "Я радий, що вам подобається!",
            "😡": "Щось вас турбує?",
            "😎": "Круто!"
        }
        for emoji in emoji_responses:
            if emoji in text:
                response = emoji_responses[emoji]
                await update.message.reply_text(response)
                self.log_message(f"User (Emoji): {text}")
                self.log_message(f"Bot: {response}")
                return
        await update.message.reply_text("Цей смайлик не підтримується.")

    async def admin_menu(self, update, context):
        if context.args and context.args[0] == self.admin_password:
            keyboard = [
                [InlineKeyboardButton("Переглянути переписки", callback_data='view_chats')],
                [InlineKeyboardButton("Надіслати повідомлення", callback_data='send_message')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Меню адміністратора:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Неправильний пароль.")

    async def start(self, update, context):
        user_id = update.effective_chat.id
        if user_id not in self.user_data:
            self.user_data[user_id] = {"started": True}
            await self.help(update, context)
            await self.settings(update, context)
        else:
            keyboard = [
                [InlineKeyboardButton("Налаштування", callback_data='settings')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            welcome_text = "Привіт! Це ваш помічник. Налаштуйте режим та мову."
            await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def help(self, update, context):
        help_text = (
            "/start - Почати роботу з ботом.\n"
            "/help - Отримати допомогу.\n"
            "/info - Отримати інформацію.\n"
            "/time - Поточний час.\n"
            "/date - Поточна дата.\n"
            "/settings - Налаштування.\n"
            "/log Admin12 - Меню адміністратора.\n"
        )
        await update.message.reply_text(help_text)

    async def settings(self, update, context):
        keyboard = [
            [InlineKeyboardButton("Текстовий режим", callback_data='text')],
            [InlineKeyboardButton("Голосовий режим", callback_data='voice')],
            [InlineKeyboardButton("Українська", callback_data='uk')],
            [InlineKeyboardButton("English", callback_data='en')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Налаштування:", reply_markup=reply_markup)

    async def button(self, update, context):
        query = update.callback_query
        data = query.data
        if data == "text":
            self.mode = "text"
            await query.edit_message_text(text="Режим змінено на текстовий." if self.language == "uk" else "Mode changed to text.")
        elif data == "voice":
            self.mode = "voice"
            await query.edit_message_text(text="Режим змінено на голосовий." if self.language == "uk" else "Mode changed to voice.")
        elif data == "uk":
            self.language = "uk"
            await query.edit_message_text(text="Мову змінено на українську.")
        elif data == "en":
            self.language = "en"
            await query.edit_message_text(text="Language changed to English.")
        elif data == "view_chats":
            await self.show_chats(update, context)
        elif data == "send_message":
            await self.send_message(update, context)

    async def show_chats(self, update, context):
        with open(self.messages_file, "r", encoding="utf-8") as file:
            messages = file.readlines()
        chat_text = "".join(messages[-10:])  # Показуємо останні 10 записів
        await update.message.reply_text("Ось останні переписки:\n" + chat_text)

    async def send_message(self, update, context):
        await update.message.reply_text("Функція на стадії розробки.")

    async def send_voice_response(self, update, response):
        tts = gTTS(response, lang=self.language)
        tts.save("response.mp3")
        await update.message.reply_voice(voice=open("response.mp3", "rb"))
        os.remove("response.mp3")

    def generate_response(self, text):
        if text in self.custom_commands:
            return self.custom_commands[text]
        else:
            return "Це тестова відповідь. Додайте свої команди."

    def run(self):
        self.application.run_polling()

    # Налаштування логування
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


    
# Приклад запуску
if __name__ == "__main__":
    bot_token = "7255862476:AAFTZAauzEvCVXACq5rlA4PQuGGUjdAtseM"
    chat_id = "7255862476"
    assistant = TextAssistant(bot_token, chat_id)
    assistant.run()
