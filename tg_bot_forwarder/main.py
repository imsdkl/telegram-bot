from app.models import *
from app.notification import *
from telethon import TelegramClient, sync, events
from telethon.errors import PeerIdInvalidError, AuthKeyUnregisteredError
from telethon.sessions import StringSession
from sentry_sdk import set_tag
import re 
import os
import datetime
import sentry_sdk
import psycopg2
import sys
import requests

SYSTEM_VERSION = "4.16.30-vxCUSTOM"

API_ID = os.environ.get('API_ID', 111)
API_HASH = os.environ.get('API_HASH', 'aaa')

chat_card_xabar_id = int(os.environ.get('CHAT_XABAR_ID', 915326936))
chat_humo_id       = int(os.environ.get('CHAT_HUMO_ID', 856254490))
chat_to_id         = int(os.environ.get('CHAT_TO_ID', 0))
phone_number       = os.environ.get('PHONE_NUMBER', '777')
url                = os.environ.get('URL', 'https://example.com/api')

Bot.ensure_connection()
bot            = Bot.get_or_none(Bot.number == phone_number)
session_string = bot.session_string

set_tag("phone_number", phone_number)

if ((phone_number == None) or (chat_card_xabar_id == 0) or (chat_humo_id == 0) or (session_string == None)):
    print(f'phone_number: {phone_number}')
    print(f'chat_card_xabar_id: {chat_card_xabar_id}')
    print(f'chat_humo_id: {chat_humo_id}')
    print(f'session_string: {session_string}')
    exit(100)

client = TelegramClient(StringSession(session_string), API_ID, API_HASH,system_version=SYSTEM_VERSION)

async def filter(event):
    # match = re.fullmatch(r'^test.*', event.raw_text)
    # return match
    # TODO: написать фильтр сообщений
    return True

@client.on(events.NewMessage(incoming=True, chats = [chat_card_xabar_id, chat_humo_id]))
async def normal_handler(event):
    message = event.message.to_dict()['message']

    data = {
        "from": bot.platform,
        "content": message
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": bot.token
    }

    response = requests.post(url, json=data, headers=headers)

    if chat_to_id != 0:
        await client.forward_messages(chat_to_id, event.message)

    print(message)

print('Bot started')
try:
    bot.state = 'run'
    bot.save()
    Bot.close_connection()

    client.start()
    client.run_until_disconnected()
except AuthKeyUnregisteredError as e:
    Bot.ensure_connection()
    bot.state = 'error_auth_need'
    bot.save()
    Bot.close_connection()

    print('Bot Failed AuthKeyUnregisteredError')
    print(e.message, e.args)

    exit(30)
except PeerIdInvalidError as e:
    Bot.ensure_connection()
    bot.state = 'error_auth_need'
    bot.save()
    Bot.close_connection()

    print('Bot Failed PeerIdInvalidError')
    print(e.message, e.args)

    exit(30)
except Exception as e:
    Bot.ensure_connection()
    bot.state = 'error'
    bot.save()
    Bot.close_connection()

    print(e.message, e.args)
    exit(30)