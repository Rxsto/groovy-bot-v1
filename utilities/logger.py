import datetime
import os
import time
import aiohttp
import asyncio
import discord

from discord import Webhook, AsyncWebhookAdapter

from enum import Enum

from utilities.config import Config


class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    CRITICAL = 50


def debug(message):
    asyncio.get_event_loop().create_task(log(LogLevel.DEBUG, message))


def info(message):
    asyncio.get_event_loop().create_task(log(LogLevel.INFO, message))


def warn(message):
    asyncio.get_event_loop().create_task(log(LogLevel.WARN, message))


def error(message, exception: Exception = None):
    asyncio.get_event_loop().create_task(log(LogLevel.ERROR, message, exception))


def critical(message, exception: Exception = None):
    asyncio.get_event_loop().create_task(log(LogLevel.CRITICAL, message, exception))


def init():
    if not os.path.exists('logs/'):
        os.makedirs('logs/')
    file = open(f'logs/obstBot_{time.strftime("%d-%m-%Y")}.log', "a")
    own_time = time.strftime("%H:%M:%S")
    init_time = time.strftime("%c")
    file.write(f'[{own_time}] [INFO] ------------------------------------------------------------------\n')
    file.write(f'[{own_time}] [INFO] Initialized logging file while booting on {init_time}\n')


async def log(level, message, exception: Exception = None):
    file = open(f'logs/obstBot_{time.strftime("%d-%m-%Y")}.log', "a")
    own_time = time.strftime("%H:%M:%S")
    formatted_message = f'[{own_time}] [{level.name}] {message}'
    print(formatted_message)
    file.write(formatted_message + '\n')
    if exception is not None:
        exception_string = f'{exception.__class__.__name__}: {exception}'
        print(exception_string)
        file.write(exception_string + '\n')
        async with aiohttp.ClientSession() as session:
            error_hook = Webhook.from_url(Config().get_config()['webhooks']['error'],
                                          adapter=AsyncWebhookAdapter(session))
            await error_hook.send(embed=discord.Embed(
                title=":no_entry_sign: An internal error occurred!",
                timestamp=datetime.datetime.now(),
                color=0xf22b2b,
                description=f'```{exception_string}```'
            ))

    file.close()
