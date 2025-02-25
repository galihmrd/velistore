from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URL
import dns.resolver

dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers=['8.8.8.8']

class Database:
    def __init__(self, uri):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client["saldo_velis"]
        self.col = self.db.saldo  # Mengganti koleksi menjadi 'menu'

    async def add_balance(self, uid, credits, receipt):
        if not await self.get_balance(uid):
            await self.col.insert_one({"uid": uid, "credits": credits, "receipt": receipt})
        else:
            await self.update_balance(uid, credits, receipt)

    async def get_balance(self, uid):
        balance_item = await self.col.find_one({'uid': uid})
        return balance_item

    async def get_all_balance(self):
        all_balance = []
        async for balance_item in self.col.find({}):
            all_balance.append(balance_item)
        return all_balance

    async def update_balance(self, uid, credits=None, receipt=None):
        update_fields = {}
        if credits is not None:
            update_fields['credits'] = credits
        if receipt is not None:
            update_fields['receipt'] = receipt
        if update_fields:
            await self.col.update_one({'uid': uid}, {'$set': update_fields})

    async def delete_balance(self, uid):
        await self.col.delete_many({'uid': uid})

credit_db = Database(DB_URL)
print("Database started...")
