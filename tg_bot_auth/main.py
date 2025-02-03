import contextlib
import re
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

from telethon import TelegramClient, errors
from telethon.sessions import StringSession

from app.buttons import f_userbots, f_main
from app.docker_service import docker_build_and_run, docker_restart, docker_stop_and_remove
from app.db import BotUser, BOT_TOKEN, create_tables, admins

logging.basicConfig(filename='logs.log', filemode='a', level=logging.INFO)


# ------------------------------------------------------------------------------
# Aiogram FSM states
# ------------------------------------------------------------------------------
class RegisterStates(StatesGroup):
    NAME = State()
    PHONE = State()
    API_ID = State()
    API_HASH = State()
    CODE = State()
    TWOFA = State()
    TOKEN = State()


# Keep Telethon client instances in memory
clients = {}


async def _create_telethon_client(user: BotUser) -> TelegramClient:
    """
    Create a new Telethon client session *without signing in*.
    We'll do sign_in later when we get the code.
    """
    session = StringSession()  # new session
    client = TelegramClient(
        session=session,
        api_id=user.api_id,
        api_hash=user.api_hash,
        # system_version=SYSTEM_VERSION
    )
    await client.connect()
    await client.send_code_request(user.number, force_sms=True)
    clients[str(user.id)] = client
    return client


async def _get_telethon_client(user: BotUser) -> TelegramClient:
    """
    Get existing Telethon client from memory dict, or create if missing.
    """
    if str(user.id) in clients:
        return clients[str(user.id)]
    return await _create_telethon_client(user)


# ------------------------------------------------------------------------------
# Handlers
# ------------------------------------------------------------------------------
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id in admins:
        await message.answer("Hello! What do you want to do?", reply_markup=f_main())
    else:
        await message.answer("Hi! What do you want to do?")
        unknown_user = message.from_user
        await bot.send_message(
            chat_id=admins[0], text=f"New user: {unknown_user.username}, first_name: {unknown_user.first_name}"
        )
    return


async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    BotUser.ensure_connection()
    state_data = await state.get_data()
    user = BotUser.get_or_none(BotUser.id == state_data["id"])
    user.name = name
    user.save()
    BotUser.close_connection()

    await message.answer("Телефон уже зарегистрирован. Теперь введите ваш API_ID (число).")
    await state.set_state(RegisterStates.API_ID)


async def process_phone_number(message: Message, state: FSMContext):
    """
    2) Save phone to DB, then ask for API_ID
    """
    phone = re.sub(r"[^\d+]", "", message.text.strip())
    BotUser.ensure_connection()
    user = BotUser.get_or_none(BotUser.number == phone)

    if user is None:
        BotUser.create(number=phone, state="initialized", platform="UZCARD")
        user = BotUser.get_or_none(BotUser.number == phone)
        await state.set_data({"id": user.id})
        BotUser.close_connection()
        await message.answer("Отлично! Введите имя пользователя:")
        await state.set_state(RegisterStates.NAME)
    else:
        await state.update_data({"id": user.id})
        if user.api_id and user.api_hash:
            try:
                client = await _create_telethon_client(user)
                user.state = "await_code"
                user.save()
            except Exception as e:
                logging.error(f"Error creating Telethon client: {e}", exc_info=True)
                await message.answer("Ошибка создания клиента. Попробуйте позднее.")
                user.state = "error_client_creation"
                user.save()
                await state.clear()
                BotUser.close_connection()
                return
            await message.answer(
                "Телефон уже зарегистрирован. Введите код, полученный в Telegram (формат 'x x x x x')."
            )
            await state.set_state(RegisterStates.CODE)
        else:
            await message.answer("Телефон уже зарегистрирован. Теперь введите ваш API_ID (число).")
            await state.set_state(RegisterStates.API_ID)
        BotUser.close_connection()


async def process_api_id(message: Message, state: FSMContext):
    """
    3) Store API_ID in DB, ask for API_HASH
    """
    if not message.text.isdigit():
        await message.answer("API_ID должен быть числом. Повторите ввод:")
        return

    api_id = int(message.text.strip())
    state_data = await state.get_data()

    BotUser.ensure_connection()
    user = BotUser.get_or_none(BotUser.id == state_data["id"])
    if user is None:
        await message.answer("Пользователь не найден. Начните /start заново.")
        BotUser.close_connection()
        await state.clear()
        return

    user.api_id = api_id
    user.save()
    BotUser.close_connection()

    await message.answer("API_ID сохранён. Теперь введите ваш API_HASH (строка).")
    await state.set_state(RegisterStates.API_HASH)


async def process_api_hash(message: Message, state: FSMContext):
    """
    4) Store API_HASH in DB,
       THEN create Telethon client session immediately,
       THEN ask user for confirmation code
    """
    api_hash = message.text.strip()
    state_data = await state.get_data()

    BotUser.ensure_connection()
    user = BotUser.get_or_none(BotUser.id == state_data["id"])
    if user is None:
        await message.answer("Пользователь не найден. Начните /start заново.")
        BotUser.close_connection()
        await state.clear()
        return

    user.api_hash = api_hash
    user.save()

    # Now that we have phone, api_id, api_hash => create Telethon client
    try:
        client = await _create_telethon_client(user)
        # We do not do sign_in here yet. We'll do it after we get the code.

        await message.answer(
            "API_HASH сохранён. Клиент создан.\n"
            "Теперь введите код, полученный в Telegram (формат 'x x x x x')."
        )
        user.state = "await_code"
        user.save()

    except Exception as e:
        logging.error(f"Error creating Telethon client: {e}", exc_info=True)
        await message.answer("Ошибка создания клиента. Попробуйте позднее.")
        user.state = "error_client_creation"
        user.save()
        await state.clear()
        BotUser.close_connection()
        return

    BotUser.close_connection()
    await state.set_state(RegisterStates.CODE)


async def process_code(message: Message, state: FSMContext):
    """
    5) Use Telethon to sign_in with phone + code.
       If 2FA is needed, we switch to TWOFA state.
       If successful, store session_string.
    """
    code = re.sub(r"\s+", "", message.text.strip())
    state_data = await state.get_data()

    BotUser.ensure_connection()
    user = BotUser.get_or_none(BotUser.id == state_data["id"])
    BotUser.close_connection()

    if user is None:
        await message.answer("Пользователь не найден. Начните /start заново.")
        await state.clear()
        return

    client = await _get_telethon_client(user)

    try:
        if not client.is_connected():
            await client.connect()

        await client.sign_in(phone=user.number, code=code)
        # If 2FA is needed, we catch SessionPasswordNeededError
        BotUser.ensure_connection()
        user.session_string = client.session.save()
        user.state = "authorized"
        user.save()
        BotUser.close_connection()

        await message.answer("Код подтверждён! Аккаунт авторизован.")
        await message.answer("Теперь введите полученный токен с платформы (строка):")
        await state.set_state(RegisterStates.TOKEN)

    except errors.SessionPasswordNeededError:
        await message.answer("Требуется 2FA. Введите пароль для двухфакторной аутентификации.")
        await state.set_state(RegisterStates.TWOFA)

    except errors.PhoneCodeInvalidError:
        await message.answer("Неверный код! Повторите ввод кода в формате 'x x x x x'.")
    except errors.FloodWaitError as e:
        logging.error("Flood wait error", exc_info=True)
        await message.answer(f"Слишком много запросов. Подождите {e.seconds} секунд. /start заново.")
        await state.clear()
    except Exception as e:
        logging.error(f"Sign-in error: {e}", exc_info=True)
        await message.answer("Произошла ошибка при входе. Попробуйте ещё раз позже. /start заново.")
        await state.clear()


async def process_twofa(message: Message, state: FSMContext):
    """
    6) If 2FA needed, handle it. Then store session string if success.
    """
    twofa_password = message.text.strip()
    state_data = await state.get_data()

    BotUser.ensure_connection()
    user = BotUser.get_or_none(BotUser.id == state_data["id"])
    BotUser.close_connection()

    if user is None:
        await message.answer("Пользователь не найден. Начните /start заново.")
        await state.clear()
        return

    client = await _get_telethon_client(user)
    try:
        await client.sign_in(password=twofa_password)

        user.session_string = client.session.save()
        user.twofa = twofa_password
        user.state = "authorized"
        BotUser.ensure_connection()
        user.save()
        BotUser.close_connection()

        await message.answer("2FA успешно подтверждена! Аккаунт авторизован.")
        await state.clear()

        await message.answer("Теперь введите полученный токен с платформы (строка):")
        await state.set_state(RegisterStates.TOKEN)

    except errors.PasswordHashInvalidError:
        await message.answer("Неверный пароль 2FA! Повторите ввод.")
    except Exception as e:
        logging.error(f"2FA error: {e}", exc_info=True)
        await message.answer("Ошибка при 2FA. Попробуйте позже. /start заново.")
        await state.clear()


async def process_platform_token(message: Message, state: FSMContext):
    """
    7) Store token in DB
    """
    token = message.text.strip()
    state_data = await state.get_data()

    BotUser.ensure_connection()
    user = BotUser.get_or_none(BotUser.id == state_data["id"])
    if user is None:
        await message.answer("Пользователь не найден. Начните /start заново.")
        await state.clear()
        return

    user.token = f"Bearer {token}"
    user.save()
    BotUser.close_connection()

    await message.answer("Токен сохранён.")

    success, docker_message = await docker_build_and_run(user)
    await message.answer(text=f"{'✅' if success else '❌'}\n\n{docker_message}")
    await state.clear()


async def callback_handler(query: CallbackQuery, state: FSMContext, bot: Bot):
    if query.from_user.id in admins:
        await state.clear()
        d = query.data

        if d.startswith('user.'):
            user_id = int(d.split(".")[1])

            BotUser.ensure_connection()
            user = BotUser.get_or_none(BotUser.id == user_id)
            BotUser.close_connection()

            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text='❌ Delete', callback_data=f'delete.{user_id}'))
            builder.add(InlineKeyboardButton(text='🔄 Restart', callback_data=f'restart.{user_id}'))
            builder.add(InlineKeyboardButton(text='🔙 Back', callback_data=f'back'))
            builder.adjust(2, 1, repeat=True)
            await query.message.edit_text(
                text=f"ID: {user.id}\nphone: {user.number}\nstate: {user.state}\napi_id: {user.api_id}\n"
                     f"api_hash: {user.api_hash}\nsession_string: {'YES' if user.session_string else 'NO'}\n"
                     f"token: {'YES' if user.token else 'NO' }\ntwofa: <code>{user.twofa}</code>",
                reply_markup=builder.as_markup(),
                parse_mode=ParseMode.HTML
            )
        elif d.startswith('restart.'):
            user_id = int(d.split(".")[1])

            BotUser.ensure_connection()
            user = BotUser.get_or_none(BotUser.id == user_id)
            BotUser.close_connection()
            if user is not None:
                success, docker_message = await docker_restart(user)
                await query.message.edit_text(f"{'✅' if success else '❌'}\n\n{docker_message}", reply_markup=None)
            else:
                await query.message.edit_text("User not found.", reply_markup=None)
        elif d.startswith('delete.'):
            user_id = int(d.split(".")[1])

            BotUser.ensure_connection()
            user = BotUser.get_or_none(BotUser.id == user_id)
            if user is not None:
                user.delete_instance()
                success, docker_message = await docker_stop_and_remove(user)
                await query.message.edit_text(f"{'✅' if success else '❌'}\n\n{docker_message}", reply_markup=None)
            BotUser.close_connection()
            await query.message.edit_text("User deleted.", reply_markup=None)
        elif d == 'back':
            with contextlib.suppress(TelegramBadRequest):
                await bot.delete_message(query.message.chat.id, query.message.message_id)

            BotUser.ensure_connection()
            users = BotUser.select()
            BotUser.close_connection()
            await bot.send_message(query.message.chat.id, "All userbots:", reply_markup=f_userbots(users))
    return


async def message_handler(message: Message, state: FSMContext):
    msg = message.text
    if message.from_user.id in admins:
        if msg == "All userbots":
            await state.clear()
            BotUser.ensure_connection()
            users = BotUser.select()
            BotUser.close_connection()
            await message.answer("All userbots:", reply_markup=f_userbots(users))
        elif msg == "Create userbot":
            await message.answer("Привет! Введите номер телефона (пример: +71234567890).")
            await state.set_state(RegisterStates.PHONE)
    return


async def main():
    create_tables()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(cmd_start, CommandStart())

    dp.callback_query.register(callback_handler, F.data)

    # Conversation steps
    dp.message.register(process_name, RegisterStates.NAME, F.text)
    dp.message.register(process_phone_number, RegisterStates.PHONE, F.text)
    dp.message.register(process_api_id, RegisterStates.API_ID, F.text)
    dp.message.register(process_api_hash, RegisterStates.API_HASH, F.text)
    dp.message.register(
        process_code,
        RegisterStates.CODE,
        F.text.regexp(r"^\d(\s\d){4}$")
    )
    dp.message.register(process_twofa, RegisterStates.TWOFA, F.text)
    dp.message.register(process_platform_token, RegisterStates.TOKEN, F.text)
    dp.message.register(message_handler, F.chat.type == "private", F.text)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
