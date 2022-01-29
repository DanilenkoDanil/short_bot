from binance.client import Client
from db import DataBase
from aiogram.dispatcher import FSMContext
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import json
import asyncio
import sys
# Каунтер при флете


with open("setting.json", 'r', encoding='utf8') as out:
    setting = json.load(out)
    print(setting)
    TOKEN = setting['TOKEN']
    admin_list = setting['admin_list']

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
database = DataBase('db.db')

pub = 'TmCZsJp55qJPOWgleRLsWv8VBmFq4BIBQMCy2nWQI4t48fTT7x6ums4keMXL7Azv'
pri = 'sYMXl1urFA8TlU71BvV4JeDAcs3r89bXFou2vDVDQNhudo7hW4oNJ6QNRqUb9iCG'

client = Client(pub, pri)


def change_leverage(symbol: str, leverage: int):
    client.futures_change_leverage(symbol=symbol,
                                   leverage=leverage)


def make_order_full(symbol: str, stop_price: str, leverage: int, quantity: str):
    change_leverage(symbol, leverage)

    client.futures_create_order(symbol=symbol,
                                side='BUY',
                                positionSide='BOTH',
                                type='STOP_MARKET',
                                closePosition='true',
                                timeInForce='GTC',
                                stopPrice=stop_price)

    client.futures_create_order(symbol=symbol,
                                side='SELL',
                                positionSide='BOTH',
                                type='MARKET',
                                quantity=quantity, )


def make_limit_order_full(symbol: str, stop_price: str, leverage: int, quantity: str, price: str):
    change_leverage(symbol, leverage)

    client.futures_create_order(symbol=symbol,
                                side='BUY',
                                positionSide='BOTH',
                                type='STOP_MARKET',
                                closePosition='true',
                                timeInForce='GTC',
                                stopPrice=stop_price)

    client.futures_create_order(symbol=symbol,
                                side='SELL',
                                positionSide='BOTH',
                                type='LIMIT',
                                quantity=quantity,
                                timeInForce='GTC',
                                price=price)


def new_stop_lose(symbol: str, stop_price: str):
    try:
        client.futures_create_order(symbol=symbol,
                                    side='BUY',
                                    positionSide='BOTH',
                                    type='STOP_MARKET',
                                    closePosition='true',
                                    timeInForce='GTC',
                                    stopPrice=stop_price)
    except Exception as e:
        print(e)
        return 0


def convert_to_dict(symbols: list):
    result_dict = {}
    for i in symbols:

        if i['symbol'] in result_dict.keys() and float(i['stopPrice']) > float(result_dict[i['symbol']]['stopPrice']):
            result_dict[i['symbol']] = i
        elif i['symbol'] not in result_dict.keys():
            result_dict[i['symbol']] = i
    return result_dict


def check_limit_order(symbols: list, symbol: str):
    for i in symbols:
        if i['symbol'] == symbol and i['type'] == 'LIMIT':
            return True
    return False


def count_accuracy(number: float):
    str_number = str(number)
    number_after_point = str_number.split('.')[1]
    counter = 0
    for _ in number_after_point:
        counter += 1
    return counter


def padding_figures(number: float):
    str_number = str(number)
    number_after_point = str_number.split('.')[0]
    counter = 0
    for _ in number_after_point:
        counter += 1
    if counter == 1:
        return 0
    else:
        return counter - 1


def create_nine(number_nine: int):
    final_str = '0.'
    for i in range(number_nine):
        final_str += '9'
    return float(final_str)


def get_orders():
    return convert_to_dict(client.futures_position_information())


@dp.message_handler(commands=['start'], state="*")
async def process_start_command(message: types.Message, state: FSMContext):
    if str(message.from_user.id) in admin_list:
        await bot.send_message(message.from_user.id, 'Привет', parse_mode='html')


@dp.message_handler(lambda message: '/add_symbol' in message.text)
async def help_message(message: types.Message, state: FSMContext):
    try:
        symbol = str(message.text.split(' ')[1])
        if 'USDT' not in symbol:
            symbol = symbol + "USDT"
        value = float(str(message.text.split(' ')[2]))
        dollar = float(str(message.text.split(' ')[3]))
        leverage = float(str(message.text.split(' ')[4]))
        stop_counter = float(str(message.text.split(' ')[5]))
        percent_counter = float(str(message.text.split(' ')[6]))
        if database.check_symbol(symbol):
            database.new_value(symbol, value, dollar, leverage, stop_counter, percent_counter)
        else:
            database.register(symbol, value, dollar, leverage, stop_counter, percent_counter)
        await bot.send_message(message.from_user.id, 'Символ добавлен/изменён',
                               parse_mode='html')
    except ValueError:
        await bot.send_message(message.from_user.id, 'Чтобы изменить или добавить символ вам нужнно ввести значение.',
                               parse_mode='html')


@dp.message_handler(lambda message: '/delete_symbol' in message.text)
async def help_message(message: types.Message, state: FSMContext):
    try:
        symbol = str(message.text.split(' ')[1])
        database.delete(symbol)

        await bot.send_message(message.from_user.id, 'Символ удалён.',
                               parse_mode='html')
    except Exception as e:
        print(e)


@dp.message_handler(lambda message: '/list' in message.text)
async def help_message(message: types.Message, state: FSMContext):
    try:
        symbol = database.get_symbols()
        for i in symbol.keys():
            await bot.send_message(message.from_user.id, f'{i} - {symbol[i]}',
                                   parse_mode='html')
    except Exception as e:
        print(e)


@dp.message_handler(lambda message: '/stop' in message.text)
async def help_message(message: types.Message, state: FSMContext):
    await bot.send_message(message.from_user.id, 'Бот остановлен',
                           parse_mode='html')
    sys.exit()


async def is_enabled():
    exchange = convert_to_dict(client.futures_exchange_info()['symbols'])

    while True:
        try:
            orders = get_orders()
            open_orders_no_dict = client.futures_get_open_orders()
            open_orders = convert_to_dict(open_orders_no_dict)
            targets = database.get_symbols()
            positions = convert_to_dict(client.futures_position_information())
            print('--------------------')
            for i in targets.keys():
                try:
                    if int(targets[i][2]) < float(targets[i][4]):
                        if float(positions[i]['entryPrice']) != 0 and i not in open_orders:
                            new_price = str(
                                float(positions[i]['entryPrice']) - 2 * float(exchange[i]['filters'][0]['tickSize']))
                            new_price = str(round(float(new_price), int(exchange[i]["pricePrecision"])))
                            try:
                                new_stop_lose(i, positions[i]['entryPrice'])
                                new_stop_lose(i, new_price)
                            except Exception as e:
                                print(e)
                            print(f'{i} - Добавлен стоп лосс')
                        elif i in open_orders and float(open_orders[i]['stopPrice']) < float(positions[i]['entryPrice']) <= \
                                float(orders[i]['markPrice']) and \
                                not check_limit_order(open_orders_no_dict, i)\
                                and float(positions[i]['entryPrice']) != 0:
                            new_price = str(float(positions[i]['entryPrice']) - 2 * float(exchange[i]['filters'][0]['tickSize']))
                            new_price = str(round(float(new_price), int(exchange[i]["pricePrecision"])))
                            try:
                                new_stop_lose(i, positions[i]['entryPrice'])
                                new_stop_lose(i, new_price)
                            except Exception as e:
                                print(e)
                            print(f'{i} - Апдейт стопа')
                        elif i in open_orders and float(open_orders[i]['stopPrice']) == float(positions[i]['entryPrice']) <= \
                                float(orders[i]['markPrice']) and \
                                not check_limit_order(open_orders_no_dict, i)\
                                and float(positions[i]['entryPrice']) != 0:
                            new_price = str(float(positions[i]['entryPrice']) - float(exchange[i]['filters'][0]['tickSize']))
                            new_price = str(round(float(new_price), int(exchange[i]["pricePrecision"])))
                            try:
                                new_stop_lose(i, new_price)
                            except Exception as e:
                                print(e)
                        else:
                            print(f'{i} - Уже куплен')
                        if float(positions[i]['entryPrice']) == 0 and not check_limit_order(open_orders_no_dict, i):
                            if float(orders[i]['markPrice']) > float(targets[i][0]) and int(targets[i][2]) == 0:
                                print(float(targets[i][0]))
                                print(create_nine(exchange[i]["pricePrecision"]))
                                stop_loss = str(float(targets[i][0]) + 2 * float(exchange[i]['filters'][0]['tickSize']))
                                stop_loss = str(round(float(stop_loss), int(exchange[i]["pricePrecision"])))

                                try:
                                    amount = str(round(float(targets[i][1]) / float(orders[i]['markPrice']) * targets[i][3],
                                                       int(exchange[i]['quantityPrecision'])))
                                    make_limit_order_full(i, stop_loss, targets[i][3], amount, targets[i][0])
                                    database.new_counter(i, int(targets[i][2]) + 1)
                                except Exception as e:
                                    print(e)

                                print(f'{targets[i]} - куплен!')
                            elif float(orders[i]['markPrice']) >= float(targets[i][0]):
                                stop_loss = str(float(orders[i]['markPrice']) + float(exchange[i]['filters'][0]['tickSize']))
                                print('Маркет')
                                print(orders[i]['markPrice'])
                                print(str(float(orders[i]['markPrice']) + 2 * float(exchange[i]['filters'][0]['tickSize'])))
                                stop_loss = str(round(float(stop_loss), int(exchange[i]["pricePrecision"])))
                                try:
                                    amount = str(round(float(targets[i][1])/float(orders[i]['markPrice']) * targets[i][3],
                                                       int(exchange[i]['quantityPrecision'])))
                                    make_order_full(i, stop_loss, targets[i][3], amount)
                                    database.new_counter(i, int(targets[i][2]) + 1)
                                except Exception as e:
                                    print(e)

                                print(f'{targets[i]} - куплен!')

                            else:
                                print(f"{targets[i][0]} - Не достиг нужной цены")
                    else:
                        new_price = str(float(targets[i][0]) - float(targets[i][0])/100 * float(targets[i][5]))
                        database.new_price(i, new_price)
                        database.null_counter(i)
                        print('Достигнут каунтер')
                except KeyError:
                    continue
            await asyncio.sleep(5)
        except Exception as e:
            print(e)
            for i in admin_list:
                try:
                    await bot.send_message(i, str(e))
                except Exception as a:
                    print(a)
            await asyncio.sleep(60)


async def on_startup(x):
    asyncio.create_task(is_enabled())


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp, skip_updates=True, on_startup=on_startup)

#
# client.futures_create_order(symbol='LINKUSDT',
#                             side='BUY',
#                             positionSide='BOTH',
#                             type='STOP_MARKET',
#                             closePosition='true',
#                             timeInForce='GTC',
#                             stopPrice='15.850')
#
# client.futures_create_order(symbol='LINKUSDT',
#                             side='SELL',
#                             positionSide='BOTH',
#                             type='MARKET',
#                             quantity='0.5')
