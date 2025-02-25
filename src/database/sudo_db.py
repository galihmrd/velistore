from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URL
import dns.resolver

dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers=['8.8.8.8']


class Database:
    def __init__(self, uri):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client["sudo_user"]
        self.col = self.db.user

    async def add_sudo(self, uid):
        if not await self.is_sudo_exist(uid):
            await self.col.insert_one({"uid": int(uid)})

    async def is_sudo_exist(self, uid):
        user = await self.col.find_one({'uid': int(uid)})
        return bool(user)

    async def get_all_sudo(self):
        list_users = []
        all_users = self.col.find({})
        async for user in all_users:
            list_users.append(user.get("uid"))
        return list_users

    async def delete_sudo(self, uid):
        await self.col.delete_many({'uid': int(uid)})


sudo_user_db = Database(DB_URL)
print("Database started...")
