from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URL
import dns.resolver

dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers=['8.8.8.8']

class Database:
    def __init__(self, uri):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client["stock_product"]
        self.col = self.db.stock

    async def add_stock(self, key, data):
        list_data = []
        if not await self.is_stock_exist(key):
            list_data.append(data)
            await self.col.insert_one({"key": key, "stock": list_data})
        else:
            stock = await self.get_stock(key)
            list_data = stock.get("stock")
            if not data in list_data:
                list_data.append(data)
                await self.update_stock(key, list_data)
            else:
                raise Exception("Data sudah ada dalam database.")

    async def is_stock_exist(self, key):
        menu_item = await self.col.find_one({'key': key})
        return bool(menu_item)

    async def get_stock(self, key):
        menu_item = await self.col.find_one({'key': key})
        if menu_item is None:
            return {}
        return menu_item

    async def remove_item(self, key, data):
        if await self.is_stock_exist(key):
            stock = await self.get_stock(key)
            list_data = stock.get("stock")
            list_data.remove(data)
            await self.update_stock(key, list_data)

    async def get_all_stocks(self):
        all_menus = []
        async for menu_item in self.col.find({}):
            all_menus.append(menu_item)
        return all_menus

    async def update_stock(self, key, data=None):
        update_fields = {}
        if data is not None:
            update_fields['stock'] = data
        if update_fields:
            await self.col.update_one({'key': key}, {'$set': update_fields})

    async def delete_stock(self, key):
        await self.col.delete_many({'key': key})


stocks_db = Database(DB_URL)
print("Database started...")
