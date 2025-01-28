from app.models import *
import asyncio
from telethon import TelegramClient, sync, events, errors
from telethon.sessions import StringSession
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import Updater, filters, Application, ContextTypes
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler
import re
import logging

# Configure logging (usually done at the beginning of your script)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


API_ID = os.environ.get('API_ID', 111)
API_HASH = os.environ.get('API_HASH', 'aaa')
TWO_STEP_PASSWORD = os.environ.get('TWO_STEP_PASSWORD', 'aaa')
SYSTEM_VERSION = "4.16.30-vxCUSTOM"
BOT_TOKEN = os.environ.get('BOT_TOKEN','111:aaa')

clients = {}

for bot in Bot.select():
  clients[bot.number] = TelegramClient(StringSession(), API_ID, API_HASH,system_version=SYSTEM_VERSION, loop=asyncio.new_event_loop())

CONTACT, CODE = range(2)

CHAT_SELECT = 10

async def start(update, context):
    contact_button = KeyboardButton(text="Мой номер телефона", request_contact=True)
    help_button = KeyboardButton(text="Помощь")
    status_button = KeyboardButton(text="Проверить статус")

    custom_keyboard = [[contact_button], [help_button, status_button]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Добро пожаловать! Выберите действие, либо отправьте номер телефона для авторизации.",
        reply_markup=reply_markup
    )
    return CONTACT


async def sign_in_async(update, context):
    user = update.message.from_user
    telegram_id = user['id']
    phone_number = re.sub('\+', '', update.message.contact['phone_number'])
    Bot.ensure_connection()
    bot = Bot.get_or_none(Bot.number == phone_number)

    if bot is None:
        await update.message.reply_text(f"Номер телефона +{phone_number} не найден", reply_markup=ReplyKeyboardRemove())

        return ConversationHandler.END

    bot.telegram_id = telegram_id

    # переписываем на пустую сессию
    clients[bot.number] = TelegramClient(
        StringSession(),
        API_ID,
        API_HASH,
        system_version=SYSTEM_VERSION,
        loop=asyncio.new_event_loop()
    )

    try:
        if clients[bot.number].is_connected():
            await clients[bot.number].disconnect()

        await clients[bot.number].connect()

        result = await clients[bot.number].sign_in(phone_number)

        bot.save()
        Bot.close_connection()

        await update.message.reply_text("Ждем пару секунд, идет подключение", reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await update.message.reply_text("Введите код для входа в Telegram в формате \"x x x x x\"", reply_markup=ReplyKeyboardRemove())

        return CODE
    except errors.FloodWait as e:
        logging.error("An error sign_in_async occurred FloodWait", exc_info=True)
        await update.message.reply_text(f"Слишком много запросов. Пожалуйста, подождите {e.seconds} секунд.")
        return ConversationHandler.END
    except Exception as e:
        logging.error("An error sign_in_async occurred", exc_info=True)
        await update.message.reply_text("Произошла ошибка при входе. Попробуйте еще раз.")
        return ConversationHandler.END

async def code(update, context) -> int:
    code = re.sub(' ', '', update.message.text)
    await update.message.reply_text(f"Проверяем авторизацию")    

    user = update.message.from_user
    telegram_id = user['id']
    Bot.ensure_connection()
    bot = Bot.get_or_none(Bot.telegram_id == telegram_id)

    if bot is None:
        await update.message.reply_text(f"Бот telegram_id:{telegram_id} не найден. Cвяжитесь с администратором", reply_markup=ReplyKeyboardRemove())
    else:
        try:
            await clients[bot.number].connect()
            try:
                await clients[bot.number].sign_in(bot.number, code)
            except errors.rpcerrorlist.SessionPasswordNeededError as err:
                await clients[bot.number].sign_in(password=TWO_STEP_PASSWORD)
            bot.session_string = clients[bot.number].session.save()
            bot.state = 'authorized'
            bot.save()
            Bot.close_connection()

        except errors.rpcerrorlist.PhoneCodeInvalidError:
            await update.message.reply_text(f"Неверный код \"{code}\"!")
            await update.message.reply_text("Введите код для входа в Telegram в формате \"x x x x x\"", reply_markup=ReplyKeyboardRemove())
            return CODE
        except errors.rpcerrorlist.SessionPasswordNeededError:
            await update.message.reply_text(f"На аккаунте включена двухфакторная аутентификация.")
        except errors.rpcerrorlist.PhoneCodeExpiredError:
            await update.message.reply_text(f"Срок действия кода истек.")
        except errors.rpcerrorlis:
            await update.message.reply_text(f"Отправка кода недоступна")
        except Exception:
            logging.error("An error code occurred", exc_info=True)
            await update.message.reply_text(f"Внутренняя ошибка. Свяжитесь администратором")
        else:
            await update.message.reply_text(f"Бот авторизариован. Спасибо!")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    await update.message.reply_text("Пока.", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

async def status(update, context) -> int:
    user = update.message.from_user
    telegram_id = user['id']
    Bot.ensure_connection()
    bot = Bot.get_or_none(Bot.telegram_id == telegram_id)
    Bot.close_connection()

    if bot == None:
        await update.message.reply_text(f"Бот telegram_id:{telegram_id} не найден, свяжитесь с администратором", reply_markup=ReplyKeyboardRemove())
    else:        
        await update.message.reply_text(
            f"Номер телефона: {bot.number}\n"
            f"Авторизация: {('бот не авторизирован ❌', 'бот авторизирован ✅')[len(bot.session_string) > 5]}\n",
            reply_markup=ReplyKeyboardRemove(),
        )

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CONTACT: [MessageHandler(filters.CONTACT, sign_in_async)],
            CODE: [MessageHandler(filters.Regex("^\d{1} \d{1} \d{1} \d{1} \d{1}$"), code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(CommandHandler("status_button", status))
    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)
    print("Bot started")

main()