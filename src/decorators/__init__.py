from typing import Callable
from pyrogram import Client
from pyrogram.types import Message

LIST_ADMIN = [1317936398]

def admins_only(func: Callable) -> Callable:
    async def decorator(client: Client, message: Message):
        if message.from_user.id in LIST_ADMIN:
            return await func(client, message)
    return decorator
