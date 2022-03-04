from __future__ import annotations
from ast import List
from itertools import zip_longest

from typing import TYPE_CHECKING, Optional, Dict, Union
from constants import HEAD_GUILD

if TYPE_CHECKING:
    from bot import Whiskey

from discord.ext import commands
from discord import Message, TextChannel, User, Member
import discord
import asyncio

from .utils import TabularData


SUGGESTION_CHANNEL_ID = 849845209126535188
REACTION_EMOJI = ["\N{UPWARDS BLACK ARROW}", "\N{DOWNWARDS BLACK ARROW}"]

OTHER_REACTION = {
    "INVALID": {
        "emoji": "\N{WARNING SIGN}",
        "color": 0xFFFFE0
    },
    "ABUSE": {
        "emoji": "\N{DOUBLE EXCLAMATION MARK}",
        "color": 0xFFA500
    },
    "INCOMPLETE": {
        "emoji": "\N{WHITE QUESTION MARK ORNAMENT}",
        "color": 0xFFFFFF
    },
    "DECLINE": {
        "emoji": "\N{CROSS MARK}",
        "color": 0xFF0000
    },
    "APPROVED": {
        "emoji": "\N{WHITE HEAVY CHECK MARK}",
        "color": 0x90EE90
        }
}


class Suggest(commands.Cog):
    def __init__(self, bot: Whiskey) -> None:
        self.bot = bot

        self.suggested_messages_id: Dict[int, Message] = {}
        self.suggestion_channel = None

    def cog_check(ctx):
        return ctx.guild is not None and ctx.guild.id == HEAD_GUILD


    async def get_or_fetch_message(self, message_id: int) -> Optional[Message]:
        try:
            self.suggested_messages_id[message_id]
        except KeyError:
            if self.suggestion_channel is None:
                self.suggestion_channel = await self._fetch_channel(SUGGESTION_CHANNEL_ID)

            await self.bot.wait_until_ready()

            async for msg in self.suggestion_channel.history(
                limit=1,
                before=discord.Object(message_id + 1),
                after=discord.Object(message_id - 1),
            ):
                self.suggested_messages_id[msg.id] = msg
                return msg
        else:
            return self.suggested_messages_id[message_id]

    async def _fetch_channel(self, channel_id: int) -> Optional[TextChannel]:
        ch: Optional[TextChannel] = self.bot.get_channel(channel_id)
        if ch is None:
            await self.bot.wait_until_ready()
            ch: TextChannel = await self.bot.fetch_channel(channel_id)
        
        return ch

    async def __suggest(self, content: Optional[str]=None, **kwargs) -> Message:
        if self.suggestion_channel is None:
            self.suggestion_channel = await self._fetch_channel(SUGGESTION_CHANNEL_ID)
        msg: Message = await self.suggestion_channel.send(content, **kwargs)
        self.suggested_messages_id[msg.id] = msg
        await self.__add_bulk_reaction(msg, *REACTION_EMOJI)
        await msg.create_thread(name=f"Suggestion {msg.id}")
        return msg

    async def __notify_on_suggestion(self, ctx, *, message: Message) -> None:
        jump_url = message.jump_url
        _id = message.id
        content = (
            f"{ctx.author.mention} you suggestion being posted on {self.suggestion_channel.mention} ({self.suggestion_channel.id}).\n"
            f"To delete the suggestion typing `{ctx.clean_prefix}suggest delete {_id}` in <#829953394499780638>\n"
            f"> {jump_url}"
        )
        try:
            await ctx.author.send(content)
        except discord.Forbidden:
            pass

    async def __add_bulk_reaction(self, message: Message, *reactions: Union[discord.Emoji, str]) -> None:
        coros = [
            asyncio.ensure_future(message.add_reaction(reaction))
            for reaction in reactions
        ]
        await asyncio.wait(coros)

    async def __notify_user(self, ctx, user: Member, *, message: Message, remark: str) -> None:
        remark = remark or "No remark was given"

        content = (
            f"{user.mention} you suggestion of ID: {message.id} had being updated.\n"
            f"By: {ctx.author} (`{ctx.author.mention}`)\n"
            f"Remark: {remark}\n"
            f"> {message.jump_url}"
        )
        try:
            await ctx.author.send(content)
        except discord.Forbidden:
            pass

    @commands.group(invoke_without_command=True)
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def suggest(self, ctx, *, suggestion: commands.clean_content=None):
        """Suggest something. Abuse of the command may result in required mod actions"""

        if not ctx.invoked_subcommand:
            embed = discord.Embed(
                description=suggestion, timestamp=ctx.message.created_at, color=0xADD8E6
            )
            embed.set_author(
                name=str(ctx.author),
                icon_url=ctx.author.display_avatar.url
            )
            embed.set_footer(
                text=f"Author ID: {ctx.author.id}",
                icon_url=ctx.guild.icon.url
            )
            msg = await self.__suggest(embed=embed)
            await self.__notify_on_suggestion(ctx, msg)
            await ctx.message.delete(delay=0)
    

    @suggest.command(name="delete")
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def suggest_delete(self, ctx, *, messageID: int):
        """To delete the suggestion you suggested"""

        msg = await self.get_or_fetch_message(messageID)
        if not msg:
            return await ctx.send(
                f"Can not find message of ID `{messageID}`. Probably already deleted, or `{messageID}` is invalid"
            )

        if ctx.channel.permissions_for(ctx.author).manage_messages:
            await msg.delete(delay=0)
            await ctx.send("Done", delete_after=5)
            return
        
        if int(msg.embeds[0].footer.text.split(":")[1]) != ctx.author.id:
            return await ctx.send(f"You don't own that 'suggestion'")
        
        await msg.delete(delay=0)
        await ctx.send("Done", delete_after=5)

    @suggest.command(name="stats")
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def suggest_status(self, ctx, *, messageID: int):
        """To get the statistics os the suggestion"""

        msg = await self.get_or_fetch_message(messageID)
        if not msg:
            return await ctx.send(
                f"Can not find message of ID `{messageID}`. Probably already deleted, or `{messageID}` is invalid"
            )
        
        table = TabularData()
        table.set_columns(["Upvote", "Downvote"])
        upvoter = []
        downvoter = []
        for reaction in msg.reactions:
            if str(reaction.emoji) == "\N{UPWARDS BLACK ARROW}":
                upvoter = await reaction.users().flatten()
            elif str(reaction.emoji) == "\N{DOWNWARDS BLACK ARROW}":
                downvoter = await reaction.users().flatten()
        table.add_rows(zip_longest(upvoter, downvoter, fillvalue=''))
        
        conflict = [i for i in upvoter + downvoter if i not in upvoter or i not in downvoter]

        embed = discord.Embed()
        embed.description = f"```\n{table.render()}```"
        if conflict:
            embed.add_field(name=f"Conflit in Reaction: {len(conflict)}", value=", ".join([str(i) for i in conflict]))
        if msg.content:
            embed.add_field(name="Flagged", value=msg.content)
        await ctx.send(content=msg.jump_url, embed=embed)


    @suggest.command(name="note", aliases=["remark"])
    @commands.has_permissions(manage_messages=True)
    async def add_note(self, ctx, messageID: int, *, remark: str):
        """To add a note in suggestion embed"""
        msg = await self.get_or_fetch_message(messageID)
        if not msg:
            return await ctx.send(
                f"Can not find message of ID `{messageID}`. Probably already deleted, or `{messageID}` is invalid"
            )
        embed = msg.embeds[0]
        embed.clear_fields()
        embed.add_field(name="Remark", value=remark[:250])
        await msg.edit(embed=embed)

        user_id = int(embed.footer.text.split(":")[1])
        user = ctx.guild.get_member(user_id)
        await self.__notify_user(ctx, user, message=msg, remark=remark)

        await ctx.send("Done", delete_after=5)


    @suggest.command(name="clear", aliases=["cls"])
    @commands.has_permissions(manage_messages=True)
    async def clear_suggestion_embed(self, ctx, messageID: int, *, remark: str):
        """To remove all kind of notes and extra reaction from suggestion embed"""
        msg = await self.get_or_fetch_message(messageID)
        if not msg:
            return await ctx.send(
                f"Can not find message of ID `{messageID}`. Probably already deleted, or `{messageID}` is invalid"
            )
        embed = msg.embeds[0]
        embed.clear_fields()
        embed.color = 0xADD8E6
        await msg.edit(embed=embed)

        for reaction in msg.reactions:
            if str(reaction.emoji) not in REACTION_EMOJI:
                await msg.clear_reaction(reaction.emoji)

        await ctx.send("Done", delete_after=5)


    @suggest.command(name="flag")
    @commands.has_permissions(manage_messages=True)
    async def suggest_flag(self, ctx, messageID, flag: str):
        """To flag the suggestion.
        
        Avalibale Flags :-
        - INVALID
        - ABUSE
        - INCOMPLETE
        - DECLINE
        - APPROVED
        """
        msg = await self.get_or_fetch_message(messageID)
        if not msg:
            return await ctx.send(
                f"Can not find message of ID `{messageID}`. Probably already deleted, or `{messageID}` is invalid"
            )
        flag = flag.upper()
        try:
            payload = OTHER_REACTION[flag]
        except KeyError:
            return await ctx.send("Invalid Flag")

        embed = msg.embeds[0]
        embed.color = payload["color"]

        user_id = int(embed.footer.text.split(":")[1])
        user = ctx.guild.get_member(user_id)
        await self.__notify_user(ctx, user, message=msg, remark="")

        content = f"Flagged: {flag} | {payload['emoji']}"
        await msg.edit(content=content, embed=embed)
        await ctx.send("Done", delete_after=5)

    @commands.Cog.listener(name="on_raw_message_delete")
    async def suggest_msg_delete(self, payload):
        if self.suggestion_channel is None:
            self.suggestion_channel = await self._fetch_channel()
        
        if self.suggestion_channel.id != payload.channel_id:
            return

        if payload.message_id in self.suggested_messages_id:
            del self.suggested_messages_id[payload.message_id]


def setup(bot: Whiskey):
    bot.add_cog(Suggest(bot))