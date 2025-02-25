from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URL
import dns.resolver

dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers=['8.8.8.8']

class Database:
    def __init__(self, uri):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client["tikmedia"]
        self.col = self.db.menu  # Mengganti koleksi menjadi 'menu'

    async def add_menu(self, key, name, price, desc):
        if not await self.is_menu_exist(key):
            await self.col.insert_one({"key": key, "name": name, "price": price, "desc": desc})
        else:
            await self.update_menu(key, name, price, desc)

    async def is_menu_exist(self, key):
        menu_item = await self.col.find_one({'key': key})
        return bool(menu_item)

    async def get_menu(self, key):
        menu_item = await self.col.find_one({'key': key})
        return menu_item

    async def get_all_menus(self):
        all_menus = []
        async for menu_item in self.col.find({}):
            all_menus.append(menu_item)
        return all_menus

    async def update_menu(self, key, name=None, price=None, desc=None):
        update_fields = {}
        if name is not None:
            update_fields['name'] = name
        if price is not None:
            update_fields['price'] = price
        if desc is not None:
            update_fields['desc'] = desc
        if update_fields:
            await self.col.update_one({'key': key}, {'$set': update_fields})

    async def delete_menu(self, key):
        await self.col.delete_many({'key': key})

menu_db = Database(DB_URL)
print("Database started...")
