from typing import List

from aiogram.types import InlineKeyboardButton, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.db import BotUser


def f_main():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Create userbot"))
    builder.add(KeyboardButton(text="All userbots"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def f_userbots(users: List[BotUser]):
    builder = InlineKeyboardBuilder()
    for user in users:
        builder.add(
            InlineKeyboardButton(text=f"{user.id} | {user.number}, [{user.state}]", callback_data=f"user.{user.id}")
        )
    builder.adjust(2, repeat=True)
    return builder.as_markup()
