from telethon.sync import TelegramClient
from telethon import events
import json
import re
import time
import random
import os
import shutil
import asyncio

status = False

with open("setting.json", 'r', encoding='utf8') as out:
    setting = json.load(out)

    client = TelegramClient(
        setting['account']['session'],
        setting['account']['api_id'],
        setting['account']['api_hash']
    )

    client.start()

    dialogs = client.get_dialogs()

    for index, dialog in enumerate(dialogs):
        if index < 250:
            print(f'[{index}] {dialog.name}')

    from_channel = dialogs[int(input("Введите номер канала для парсинга: "))]
    to_channel = dialogs[int(input("Введите номер канала для пересылки: "))]

    @client.on(events.NewMessage(from_channel))
    async def handler(event):
        print(event.message)
        if event.message.reply_to is not None and 'entry' not in str(event.message.text).lower():
            await client.send_message(to_channel, event.message.text)
            print('Переслано')

    client.run_until_disconnected()
