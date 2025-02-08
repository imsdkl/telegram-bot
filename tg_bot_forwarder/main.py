import os
import requests
from sentry_sdk import set_tag
from telethon import TelegramClient, events
from telethon.errors import PeerIdInvalidError, AuthKeyUnregisteredError
from telethon.sessions import StringSession

from app.models import BotUser

chat_card_xabar_id = int(os.environ.get('CHAT_XABAR_ID', 915326936))
chat_humo_id = int(os.environ.get('CHAT_HUMO_ID', 856254490))
chat_to_id = int(os.environ.get('CHAT_TO_ID', 0))
USER_ID = int(os.environ.get('USER_ID', 0))
url = os.environ.get('URL', 'https://example.com/api')

BotUser.ensure_connection()

user = BotUser.get_or_none(BotUser.id == USER_ID)
session_string = user.session_string
API_ID = user.api_id
API_HASH = user.api_hash
phone_number = user.number

set_tag("phone_number", phone_number)

if phone_number is None or chat_card_xabar_id == 0 or chat_humo_id == 0 or session_string is None:
    print(f'phone_number: {phone_number}')
    print(f'chat_card_xabar_id: {chat_card_xabar_id}')
    print(f'chat_humo_id: {chat_humo_id}')
    print(f'session_string: {session_string}')
    exit(100)

client = TelegramClient(StringSession(session_string), API_ID, API_HASH)


@client.on(events.NewMessage(incoming=True, chats=[chat_card_xabar_id, chat_humo_id]))
async def normal_handler(event):
    message = event.message.to_dict()['message']
    telegram_id = event.message.to_dict()['from_id']
    BotUser.ensure_connection()
    user.telegram_id = telegram_id
    user.save()
    BotUser.close_connection()

    data = {"from": user.platform, "content": message}

    headers = {"Content-Type": "application/json", "Authorization": user.token}

    response = requests.post(url, json=data, headers=headers)

    if response.status_code != 200:
        print(f"Status code: {response.status_code}, Response: {response.text}")

    if chat_to_id != 0:
        await client.forward_messages(chat_to_id, event.message)

    print(message)


print('Bot started')
try:
    user.state = 'run'
    user.save()
    BotUser.close_connection()

    client.start()
    client.run_until_disconnected()
except AuthKeyUnregisteredError as e:
    BotUser.ensure_connection()
    user.state = 'error_auth_need'
    user.save()
    BotUser.close_connection()

    print('BotUser Failed AuthKeyUnregisteredError')
    print(e.message, e.args)
    exit(30)

except PeerIdInvalidError as e:
    BotUser.ensure_connection()
    user.state = 'error_auth_need'
    user.save()
    BotUser.close_connection()

    print('BotUser Failed PeerIdInvalidError')
    print(e.message, e.args)
    exit(30)

except Exception as e:
    BotUser.ensure_connection()
    user.state = 'error'
    user.save()
    BotUser.close_connection()

    print()
    print(e.args)
    exit(30)
