from typing import Callable
from pyrogram import Client
from pyrogram.types import Message
from src.database.sudo_db import sudo_user_db

def admins_only(func: Callable) -> Callable:
    async def decorator(client: Client, message: Message):
        sudo = await sudo_user_db.is_sudo_exist(message.from_user.id)
        if sudo:
            return await func(client, message)

    return decorator
