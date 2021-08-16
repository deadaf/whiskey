import time
import os
import asyncio
import aiohttp
import discord
from tortoise import Tortoise
import config, cogs

from async_property import async_property
from discord.ext import commands

from discord.ext.commands.errors import (
    CommandNotFound,
)


os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"


class Whiskey(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=commands.when_mentioned_or("?"),
            strip_after_prefix=True,
            case_insensitive=True,
            intents=discord.Intents.all(),
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, replied_user=False, users=False),
            activity=discord.Activity(type=discord.ActivityType.watching, name="Are you drunk?"),
            **kwargs,
        )

        for cog in cogs.__loadable__:
            self.load_extension(cog)

        self.load_extension("jishaku")

        asyncio.get_event_loop().run_until_complete(self.init_whiskey())
        self.loop = asyncio.get_event_loop()

        self._BotBase__cogs = commands.core._CaseInsensitiveDict()

        self.support_channels = set()

    @property
    def config(self):
        """import and return config.py"""
        return __import__("config")

    @property
    def constants(self):
        """import and return constants.py"""
        return __import__("constants")

    @property
    def db(self):
        return Tortoise.get_connection("default")._pool

    async def init_whiskey(self):
        self.session = aiohttp.ClientSession(loop=self.loop)
        await Tortoise.init(self.config.TORTOISE)
        await Tortoise.generate_schemas(safe=True)

        for mname, model in Tortoise.apps.get("models").items():
            model.bot = self

    async def on_ready(self):
        print(f"Ragnarok is coming...")

    async def close(self):
        await super().close()
        await self.session.close()

    @async_property
    async def db_latency(self):
        t1 = time.perf_counter()
        await self.db.execute("SELECT 1;")
        t2 = time.perf_counter() - t1
        return f"{t2*1000:.2f}ms"

    @async_property
    async def head_guild(self):
        return await self.getch(self.get_guild, self.fetch_guild, self.config.HEAD_GUILD)

    @staticmethod
    async def getch(get_method, fetch_method, _id):
        try:
            _result = get_method(_id) or await fetch_method(_id)
        except (discord.HTTPException, discord.Forbidden, discord.NotFound):
            return None
        else:
            return _result

    async def on_command_error(self, ctx, error):
        ignorable = (CommandNotFound,)

        if not isinstance(error, ignorable):
            return await ctx.send(error)


if __name__ == "__main__":
    Whiskey().run(config.DISCORD_TOKEN)
