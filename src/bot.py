import socket
import time
import os
import asyncio
import traceback
from typing import Any, Callable
import aiohttp
import discord
from tortoise import Tortoise
import config, cogs

from cogs.utils import HelpCommand
from async_property import async_property
from discord.ext import commands

from discord.ext.commands.errors import (
    CommandNotFound,
)

from models import Response


os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"


class Whiskey(commands.Bot):
    def __init__(self, **kwargs) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or("?"),
            strip_after_prefix=True,
            case_insensitive=True,
            intents=discord.Intents.all(),
            help_command=HelpCommand(),
            allowed_mentions=discord.AllowedMentions.none(),
            activity=discord.Activity(type=discord.ActivityType.playing, name="Are you drunk?"),
            **kwargs,
        )
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()

        self.persistent_views_added = False
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

    async def setup_hook(self) -> None:
        await self.load_extension("jishaku")
        for cog in cogs.__loadable__:
            try:
                await self.load_extension(cog)
            except Exception:
                traceback.print_exc()
        await self.init_whiskey()

    async def init_whiskey(self) -> None:
        self.session = aiohttp.ClientSession()
        await Tortoise.init(self.config.TORTOISE)
        await Tortoise.generate_schemas(safe=True)

        for mname, model in Tortoise.apps.get("models").items():
            model.bot = self

        async for record in Response.all():
            [self.support_channels.add(channel_id) for channel_id in record.valid_channel_ids]

    async def on_ready(self) -> None:
        if not self.persistent_views_added:
            from cogs.views import SelfRoles

            self.add_view(SelfRoles(), message_id=884468160655425536)

            self.persistent_views_added = True

        print(f"Ragnarok is coming...")

    async def close(self):
        await super().close()
        await self.session.close()

    @async_property
    async def db_latency(self) -> str:
        t1 = time.perf_counter()
        await self.db.execute("SELECT 1;")
        t2 = time.perf_counter() - t1
        return f"{t2*1000:.2f}ms"

    @async_property
    async def head_guild(self) -> discord.Guild:
        return await self.getch(self.get_guild, self.fetch_guild, self.config.HEAD_GUILD)

    @staticmethod
    async def getch(get_method: Callable, fetch_method: Callable, _id: int) -> Any:
        try:
            _result = get_method(_id) or await fetch_method(_id)
        except (discord.HTTPException, discord.Forbidden, discord.NotFound):
            return None
        else:
            return _result

    async def on_command_error(self, ctx, error) -> None:
        ignorable = (CommandNotFound,)

        if not isinstance(error, ignorable):
            return await ctx.send(error)





if __name__ == "__main__":
    bot = Whiskey()
    bot.run(config.DISCORD_TOKEN)

