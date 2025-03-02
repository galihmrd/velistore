from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URL
import dns.resolver

dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers=['8.8.8.8']

class Database:
    def __init__(self, uri):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client["order_completed"]
        self.col = self.db.order  # Mengganti koleksi menjadi 'menu'

    async def add_order(self, receipt_id, time, amount, data):
        if not await self.is_order_exist(receipt_id):
            await self.col.insert_one({"receipt_id": receipt_id, "time": time, "amount": amount, "data": data})
        else:
            await self.update_menu(receipt_id, time, amount, data)

    async def is_order_exist(self, receipt_id):
        receipt = await self.col.find_one({'receipt_id': receipt_id})
        return bool(receipt)

    async def get_order(self, receipt_id):
        receipt = await self.col.find_one({'receipt_id': receipt_id})
        return receipt

    async def get_all_order(self):
        all_order = []
        async for order_item in self.col.find({}):
            all_order.append(order_item)
        return all_order

    async def update_menu(self, receipt_id, time=None, amount=None, data=None):
        update_fields = {}
        if time is not None:
            update_fields['time'] = time
        if amount is not None:
            update_fields['amount'] = amount
        if data is not None:
            update_fields['data'] = data
        if update_fields:
            await self.col.update_one({'receipt_id': receipt_id}, {'$set': update_fields})

    async def delete_menu(self, receipt_id):
        await self.col.delete_many({'receipt_id': receipt_id})

orders_db = Database(DB_URL)
print("Database started...")
