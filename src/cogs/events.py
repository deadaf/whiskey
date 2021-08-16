from __future__ import annotations
import asyncio

import typing

from cogs.utils.cache import get_guild_keywords
from cogs.utils.defaults import get_best_match

if typing.TYPE_CHECKING:
    from bot import Whiskey


from discord.ext import commands
from models import ResponseData, Voice, Response
from contextlib import suppress

import discord
from constants import COLOR

from .utils import response_ignore_check


class WhiskeyEvents(commands.Cog):
    def __init__(self, bot: Whiskey):
        self.bot = bot
        self.bot.loop.create_task(self.join_vcs())
        self.bot.loop.create_task(self.fill_support_channels())

        self.reactions = ("👍", "👎")

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

        match = matches[0]

        if match.confidence >= 70:
            response = await record.data.filter(keywords__icontains=match.keyword).first()
            embed = discord.Embed(color=COLOR, description=response.content)
            embed.set_footer(text=f"Confidence: {match.confidence:.01f} ● 👍 {response.upvote} 👎 {response.downvote}")
            msg = await message.reply(embed=embed)

            for reaction in self.reactions:
                await msg.add_reaction(reaction)

            upvote, downvote = 0, 0
            try:
                react, user = await self.bot.wait_for(
                    "reaction_add",
                    check=lambda r, u: r.emoji in self.reactions and u.id == message.author.id and r.message.id == msg.id,
                    timeout=30,
                )

            except asyncio.TimeoutError:
                await msg.clear_reactions()
                return await ResponseData.filter(pk=response.id).update(uses=response.uses + 1)

            else:
                if str(react.emoji) == self.reactions[0]:
                    upvote = 1

                elif str(react.emoji) == self.reactions[1]:
                    downvote = 1

            await msg.clear_reactions()
            await ResponseData.filter(pk=response.id).update(
                upvote=response.upvote + upvote, downvote=response.downvote + downvote, uses=response.uses + 1
            )


def setup(bot):
    bot.add_cog(WhiskeyEvents(bot))
