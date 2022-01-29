import time
from sqlite3 import IntegrityError
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from binance.client import Client
from db import DataBase
import json
import asyncio

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


with open("setting.json", 'r', encoding='utf8') as out:
    setting = json.load(out)
    print(setting)
    TOKEN = setting['TOKEN']
    admin_list = setting['admin_list']

api_key = 'Hmmf4wl1KiRBtbPPIzeUVb2lI4Ltaav4zReubEetTCMT9SDSb8WwpYgUJOGQK61h'
api_secret = 'ahtoW6ZBnfibkPzAssXRX5vD7El475r8pJ2J2vYJc0SFCfQcrZLbvPyjAZuF7tAV'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

database = DataBase('db.db')
timeout = 60
percent = 2


def scan_main_value():
    client_bin = Client(api_key, api_secret)
    tickers = client_bin.get_all_tickers()
    print(tickers)
    for i in tickers:
        if i['symbol'][-4:] == 'USDT':
            print('+')
            if database.check_symbol(i['symbol']):
                database.new_value(i['symbol'], i['price'])
            else:
                database.register(i['symbol'], i['price'])


def scan_current_price():
    full_list = []
    client_bin = Client(api_key, api_secret)
    tickers = client_bin.get_all_tickers()
    base = database.get_symbols()
    for i in tickers:
        if i['symbol'][-4:] == 'USDT':
            if float(i['price']) - float(base[i['symbol']]) > float(base[i['symbol']])/100 * percent:
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                print(i['symbol'])
                print(i['price'])
                print(base[i['symbol']])
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                full_list.append([i['symbol'], i['price']])
    return full_list


@dp.message_handler(commands=['start'], state="*")
async def process_start_command(message: types.Message, state: FSMContext):
    if str(message.from_user.id) in admin_list:
        await bot.send_message(message.from_user.id, 'Привет', parse_mode='html')


@dp.message_handler(lambda message: '/change_timeout' in message.text)
async def help_message(message: types.Message, state: FSMContext):
    global timeout
    try:
        timeout = int(60*float(message.text.split(' ')[1]))
        print(timeout)
        await bot.send_message(message.from_user.id, f'Отлично! Текуший таймаунт - {int(timeout/60)} мин',
                               parse_mode='html')
    except ValueError:
        await bot.send_message(message.from_user.id, 'Чтобы изменить таймаут вам нужнно ввести число.',
                               parse_mode='html')


@dp.message_handler(lambda message: '/change_percent' in message.text)
async def help_message(message: types.Message, state: FSMContext):
    global percent
    try:
        percent = float(message.text.split(' ')[1])
        print(percent)
        await bot.send_message(message.from_user.id, f'Отлично! Текуший процент - {percent}',
                               parse_mode='html')
    except ValueError:
        await bot.send_message(message.from_user.id, 'Чтобы изменить процент вам нужнно ввести число.',
                               parse_mode='html')


async def is_enabled():
    scan_main_value()
    timer = time.time()
    while True:
        if time.time() - timer > timeout:
            print('Updat')
            scan_main_value()
            timer = time.time()
        result = scan_current_price()
        print(result)
        for admin in admin_list:
            if len(result) > 0:
                await bot.send_message(admin, str(result),
                                       parse_mode='html')
        await asyncio.sleep(1)


async def on_startup(x):
    asyncio.create_task(is_enabled())


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp, skip_updates=True, on_startup=on_startup)
