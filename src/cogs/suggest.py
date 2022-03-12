from __future__ import annotations
from itertools import zip_longest

from typing import TYPE_CHECKING, Any, Optional, Dict, Union, List
from .utils import TabularData, WrappedMessageConverter

if TYPE_CHECKING:
    from bot import Whiskey

from discord.ext import commands
from discord import Message, TextChannel, User, Member
import discord
import asyncio


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
        self.cooldown = commands.CooldownMapping.from_cooldown(
            1, 60, commands.BucketType.member
        )

    def cog_check(self, ctx):
        return ctx.guild is not None and ctx.guild.id == 746337818388987967

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

    async def _fetch_channel(self, channel_id: Optional[int]=None) -> Optional[TextChannel]:
        channel_id: int = channel_id or SUGGESTION_CHANNEL_ID
        ch: Optional[TextChannel] = self.bot.get_channel(channel_id)
        if ch is None:
            await self.bot.wait_until_ready()
            ch: TextChannel = await self.bot.fetch_channel(channel_id)
        
        return ch

    async def __suggest(self, content: Optional[str]=None, *, embed: discord.Embed, ctx: commands.Context) -> Message:
        if self.suggestion_channel is None:
            self.suggestion_channel = await self._fetch_channel(SUGGESTION_CHANNEL_ID)
        msg: Optional[Message] = await self.suggestion_channel.send(content, embed=embed)
        self.suggested_messages_id[msg.id] = msg
        await self.__add_bulk_reaction(msg, *REACTION_EMOJI)
        await msg.create_thread(name=f"Suggestion {ctx.author}")
        return msg

    async def __notify_on_suggestion(self, ctx: commands.Context, *, message: Message) -> None:
        jump_url: str = message.jump_url
        _id: int = message.id
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

    async def __notify_user(self, ctx: commands.Context, user: Member, *, message: Message, remark: str) -> None:
        remark = remark or "No remark was given"

        content = (
            f"{user.mention} you suggestion of ID: {message.id} had being updated.\n"
            f"By: {ctx.author} (`{ctx.author.id}`)\n"
            f"Remark: {remark}\n"
            f"> {message.jump_url}"
        )
        try:
            await ctx.author.send(content)
        except discord.Forbidden:
            pass


    @commands.group(aliases=["suggestion"], invoke_without_command=True)
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def suggest(self, ctx: commands.Context, *, suggestion: commands.clean_content):
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
            msg = await self.__suggest(ctx=ctx, embed=embed)
            await self.__notify_on_suggestion(ctx, message=msg)
            await ctx.message.delete(delay=0)
    

    @suggest.command(name="delete")
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def suggest_delete(self, ctx: commands.Context, *, messageID: int):
        """To delete the suggestion you suggested"""

        msg: Optional[Message] = await self.get_or_fetch_message(messageID)
        if not msg:
            return await ctx.send(
                f"Can not find message of ID `{messageID}`. Probably already deleted, or `{messageID}` is invalid"
            )
        
        if msg.author.id != self.bot.user.id:
            return await ctx.send(
                f"Invalid `{messageID}`"
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
    async def suggest_status(self, ctx: commands.Context, *, messageID: int):
        """To get the statistics os the suggestion"""

        msg: Optional[Message] = await self.get_or_fetch_message(messageID)
        if not msg:
            return await ctx.send(
                f"Can not find message of ID `{messageID}`. Probably already deleted, or `{messageID}` is invalid"
            )
        
        if msg.author.id != self.bot.user.id:
            return await ctx.send(
                f"Invalid `{messageID}`"
            )
        
        table = TabularData()
        upvoter = []
        downvoter = []
        for reaction in msg.reactions:
            if str(reaction.emoji) == "\N{UPWARDS BLACK ARROW}":
                upvoter = await reaction.users().flatten()
            elif str(reaction.emoji) == "\N{DOWNWARDS BLACK ARROW}":
                downvoter = await reaction.users().flatten()
        upvoter = [str(m) for m in upvoter]
        downvoter = [str(m) for m in downvoter]
        
        table.set_columns(["Upvote", "Downvote"])
        ls = list(zip_longest(upvoter, downvoter, fillvalue=''))
        table.add_rows(ls)

        conflict = [i for i in upvoter if i in downvoter]

        embed = discord.Embed()
        embed.description = f"```\n{table.render()}```"
        if conflict:
            embed.add_field(name=f"Conflit in Reaction: {len(conflict)}", value=", ".join([str(i) for i in conflict]))
        if msg.content:
            embed.add_field(name="Flagged", value=msg.content)
        await ctx.send(content=msg.jump_url, embed=embed)


    @suggest.command(name="note", aliases=["remark"])
    @commands.check_any(commands.has_permissions(manage_messages=True), commands.has_any_role(874328457167929386, 'Moderator'))
    async def add_note(self, ctx: commands.Context, messageID: int, *, remark: str):
        """To add a note in suggestion embed"""
        msg: Optional[Message] = await self.get_or_fetch_message(messageID)
        if not msg:
            return await ctx.send(
                f"Can not find message of ID `{messageID}`. Probably already deleted, or `{messageID}` is invalid"
            )
        
        if msg.author.id != self.bot.user.id:
            return await ctx.send(
                f"Invalid `{messageID}`"
            )
        
        embed: discord.Embed = msg.embeds[0]
        embed.clear_fields()
        embed.add_field(name="Remark", value=remark[:250])
        await msg.edit(content=msg.content, embed=embed)

        user_id = int(embed.footer.text.split(":")[1])
        user = ctx.guild.get_member(user_id)
        await self.__notify_user(ctx, user, message=msg, remark=remark)

        await ctx.send("Done", delete_after=5)


    @suggest.command(name="clear", aliases=["cls"])
    @commands.check_any(commands.has_permissions(manage_messages=True), commands.has_any_role(874328457167929386, 'Moderator'))
    async def clear_suggestion_embed(self, ctx: commands.Context, messageID: int, *, remark: str):
        """To remove all kind of notes and extra reaction from suggestion embed"""
        msg: Optional[Message] = await self.get_or_fetch_message(messageID)
        if not msg:
            return await ctx.send(
                f"Can not find message of ID `{messageID}`. Probably already deleted, or `{messageID}` is invalid"
            )
        
        if msg.author.id != self.bot.user.id:
            return await ctx.send(
                f"Invalid `{messageID}`"
            )
        
        embed: discord.Embed = msg.embeds[0]
        embed.clear_fields()
        embed.color = 0xADD8E6
        await msg.edit(embed=embed, content=None)

        for reaction in msg.reactions:
            if str(reaction.emoji) not in REACTION_EMOJI:
                await msg.clear_reaction(reaction.emoji)

        await ctx.send("Done", delete_after=5)


    @suggest.command(name="flag")
    @commands.check_any(commands.has_permissions(manage_messages=True), commands.has_any_role(874328457167929386, 'Moderator'))
    async def suggest_flag(self, ctx: commands.Context, messageID: int, *, flag: str=None):
        """To flag the suggestion.
        
        Avalibale Flags :-
        - INVALID
        - ABUSE
        - INCOMPLETE
        - DECLINE
        - APPROVED
        """
        flag = flag or "INVALID"

        msg: Optional[Message] = await self.get_or_fetch_message(messageID)
        if not msg:
            return await ctx.send(
                f"Can not find message of ID `{messageID}`. Probably already deleted, or `{messageID}` is invalid"
            )
        
        if msg.author.id != self.bot.user.id:
            return await ctx.send(
                f"Invalid `{messageID}`"
            )
        
        flag = flag.upper()
        try:
            payload: Dict[str, Union[int, str]] = OTHER_REACTION[flag]
        except KeyError:
            return await ctx.send("Invalid Flag")

        embed: discord.Embed = msg.embeds[0]
        embed.color = payload["color"]

        user_id = int(embed.footer.text.split(":")[1])
        user: Member = ctx.guild.get_member(user_id)
        await self.__notify_user(ctx, user, message=msg, remark="")

        content = f"Flagged: {flag} | {payload['emoji']}"
        await msg.edit(content=content, embed=embed)
        await ctx.send("Done", delete_after=5)


    @commands.Cog.listener(name="on_raw_message_delete")
    async def suggest_msg_delete(self, payload) -> None:
        if self.suggestion_channel is None:
            self.suggestion_channel = await self._fetch_channel()
        
        if self.suggestion_channel.id != payload.channel_id:
            return

        if payload.message_id in self.suggested_messages_id:
            del self.suggested_messages_id[payload.message_id]


    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.author.bot:
            return

        if self.suggestion_channel is None:
            self.suggestion_channel = await self._fetch_channel(SUGGESTION_CHANNEL_ID)
        
        if message.channel.id != self.suggestion_channel.id:
            return

        await self.__parse_mod_action(message)

        context: commands.Context = await self.bot.get_context(message, cls=commands.Context)
        # cmd: commands.Command = self.bot.get_command("suggest")

        # await context.invoke(cmd, suggestion=message.content)

        await self.suggest(context, suggestion=message.content)

    async def __parse_mod_action(self, message: Message) -> None:
        if not self.__is_mod(message.author):
            return

        if message.content.upper() in OTHER_REACTION:
            context: commands.Context = await self.bot.get_context(message, cls=commands.Context)
            # cmd: commands.Command = self.bot.get_command("suggest flag")

            msg: Union[Message, discord.DeletedReferencedMessage] = message.reference.resolved

            if not isinstance(msg, discord.Message):
                return

            if msg.author.id != self.bot.user.id:
                return

            # await context.invoke(cmd, msg.id, message.content.upper())
            await self.suggest_flag(context, msg.id, message.content.upper())

    def __is_mod(self, member: Member) -> bool:
        if member._roles.has(874328457167929386):
            return True

        perms: discord.Permissions = member.guild_permissions
        if any([perms.administrator, perms.manage_messages]):
            return True

        return False

def setup(bot: Whiskey):
    bot.add_cog(Suggest(bot))
