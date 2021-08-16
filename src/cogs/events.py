from __future__ import annotations

import typing

from cogs.utils.cache import get_guild_keywords
from cogs.utils.defaults import get_best_match

if typing.TYPE_CHECKING:
    from bot import Whiskey


from discord.ext import commands
from models import Voice, Response
from contextlib import suppress

import discord

from .utils import response_ignore_check


class WhiskeyEvents(commands.Cog):
    def __init__(self, bot: Whiskey):
        self.bot = bot
        self.bot.loop.create_task(self.join_vcs())
        self.bot.loop.create_task(self.fill_support_channels())

    async def join_vcs(self):
        await self.bot.wait_until_ready()
        async for record in Voice.all():
            guild = await self.bot.getch(self.bot.get_guild, self.bot.fetch_guild, record.guild_id)
            if not guild.chunked:
                self.bot.loop.create_task(guild.chunk())

            with suppress(discord.Forbidden, discord.ClientException, AttributeError):
                await guild.get_channel(record.voice_channel_id).connect()

    async def fill_support_channels(self):
        await self.bot.wait_until_ready()
        async for record in Response.all():
            for channel_id in record.valid_channel_ids:
                self.bot.support_channels.add(channel_id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot or not message.content:
            return

        if not message.channel.id in self.bot.support_channels:
            return

        channel_id = message.channel.id

        record = await Response.get_or_none(valid_channel_ids__contains=channel_id)
        if not record:
            return self.bot.support_channels.remove(channel_id)

        if response_ignore_check(message.author, record.ignored_ids):
            return

        guild_keywords = await get_guild_keywords(message.guild.id)

        matches = get_best_match(guild_keywords, message.content)
        if not matches:
            return

        await message.channel.send(matches)

        # response = await record.data.filter(keywords__icontains=keyword).first()
        # with suppress(discord.Forbidden, AttributeError):
        #     author = await self.bot.getch(self.bot.get_user, self.bot.fetch_user, response.author_id)

        #     await message.reply(f"{response.content}\n\n- {author}")


def setup(bot):
    bot.add_cog(WhiskeyEvents(bot))
