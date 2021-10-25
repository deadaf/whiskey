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
from constants import COLOR

from unicodedata import normalize
import random
from .utils import response_ignore_check


class WhiskeyEvents(commands.Cog):
    def __init__(self, bot: Whiskey):
        self.bot = bot
        self.bot.loop.create_task(self.fill_support_channels())

        self.reactions = ("👍", "👎")

    async def fill_support_channels(self):
        await self.bot.wait_until_ready()
        async for record in Response.all():
            for channel_id in record.valid_channel_ids:
                self.bot.support_channels.add(channel_id)

    @commands.Cog.listener(name="on_message")
    async def on_suggestion(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        if not message.channel.id == 849845209126535188:
            return

        if any(i in (874328457167929386, 829940691500269588) for i in (role.id for role in message.author.roles)):
            return

        await message.add_reaction("✅")
        await message.add_reaction("❌")

    @commands.Cog.listener(name="on_message")
    async def on_smart_response(self, message: discord.Message):
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

        matches = get_best_match(guild_keywords, re.sub(r"<@*#*!*&*\d+>|[^\w\s]", "", message.content))
        if not matches:
            return

        match = matches[0]

        if match.confidence >= 68.5:
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

    async def welcome_member(self, member: discord.Member):
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
        c = self.bot.get_channel(829945755644592168)
        await c.send(random.choice(_list).format(member.mention))

    async def clean_name(self, member: discord.Member):
        _n = normalize("NKFC", member.display_name)
        _n = re.sub(r"[^\w\s]", "", _n)
        return await member.edit(nick=_n if _n else "bad_nick")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not member.guild.id == 746337818388987967:
            return

        await self.clean_name(member)
        await self.welcome_member(member)

    @commands.Cog.listener(name="on_message")
    async def on_ganda_message(self, message: discord.Message):
        if not message.guild.id == 746337818388987967 or message.author.bot:
            return

        await self.clean_name(message.author)


def setup(bot):
    bot.add_cog(WhiskeyEvents(bot))
