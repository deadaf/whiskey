from __future__ import annotations
import asyncio

import typing
import re

from cogs.utils.cache import get_guild_keywords
from cogs.utils.defaults import get_best_match

if typing.TYPE_CHECKING:
    from bot import Whiskey


from discord.ext import commands
from models import ResponseData, Response

import discord
from constants import COLOR, DEADSHOT, GENERAL

from contextlib import suppress
from unicodedata import normalize
import random
from .utils import response_ignore_check
from ..constants import HEAD_GUILD


class WhiskeyEvents(commands.Cog):
    def __init__(self, bot: Whiskey) -> None:
        self.bot = bot
        self.reactions = ("\N{THUMBS UP SIGN}", "\N{THUMBS DOWN SIGN}")

    async def cog_load(self) -> None:
        await self.bot.wait_until_ready()
        async for record in Response.all():
            [self.bot.support_channels.add(channel_id) for channel_id in record.valid_channel_ids]

    @commands.Cog.listener(name="on_message")
    async def on_smart_response(self, message: discord.Message) -> None:
        if not message.guild or message.author.bot or not message.content:
            return

        if message.channel.id not in self.bot.support_channels:
            return

        channel_id = message.channel.id

        record = await Response.get_or_none(valid_channel_ids__contains=channel_id)
        if not record:
            return self.bot.support_channels.remove(channel_id)

        if response_ignore_check(message.author, record.ignored_ids):
            return

        guild_keywords = await get_guild_keywords(message.guild.id)

        matches = get_best_match(guild_keywords, re.sub(r"<@*#*!*&*\d+>|[^\w\s]", "", message.content))
        if not matches:
            return

        match = matches[0]

        if match.confidence >= 68.5:
            response = await record.data.filter(keywords__icontains=match.keyword).first()
            embed = discord.Embed(color=COLOR, description=response.content)
            embed.set_footer(text=f"Confidence: {match.confidence:.01f} ● \N{THUMBS UP SIGN} {response.upvote} \N{THUMBS DOWN SIGN} {response.downvote}")
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

    async def welcome_member(self, member: discord.Member) -> None:
        _list = [
            "{} is here.",
            "Everyone welcome {}.",
            "{} hoped into the server.",
            "Aaiye, aapka intzaar tha {}.",
            "Dekho, woh aa gya {}.",
            "A wild {} appeared.",
            "Yay you made it {}.",
            "{} joined the party.",
            "Bhai {}, daru laya hai?",
            "Bhai {} tu aagya, bahot acha laga.",
        ]
        c = self.bot.get_channel(GENERAL)
        if c is not None:
            await c.send(random.choice(_list).format(member.mention))

    async def clean_name(self, member: discord.Member) -> None:
        _n = normalize("NFKC", member.display_name).encode("ascii", "ignore").decode()
        _n = re.sub(r"[^a-zA-Z']+", " ", _n)

        _n = "imposter" if _n.lower() == "deadshot" and member.id != DEADSHOT else _n


        if _n == member.name:
            return

        with suppress(discord.HTTPException):
            return await member.edit(nick=_n or "bad_nick")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.guild.id != HEAD_GUILD:
            return
        if member.id == 731007992920539259:
            return
        await self.clean_name(member)
        # await self.welcome_member(member)

    @commands.Cog.listener(name="on_message")
    async def on_ganda_message(self, message: discord.Message) -> None:

        if message.guild and (message.guild.id != HEAD_GUILD or message.author.bot):
            return

        await self.clean_name(message.author)

    @commands.Cog.listener()
    async def on_guild_member_update(self, before: discord.Member, after: discord.Member) -> None:
        if before.guild.id != HEAD_GUILD:
            return

        if before.display_name != after.display_name:
            await self.clean_name(after)


async def setup(bot) -> None:
    await bot.add_cog(WhiskeyEvents(bot))
