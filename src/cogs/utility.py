from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from bot import Whiskey


from discord.ext.commands import command, Context, Cog
from discord import utils, Permissions


class Utility(Cog):
    def __init__(self, bot: Whiskey):
        self.bot = bot

    @command()
    async def invite(self, ctx: Context):
        """invite me"""
        await ctx.send(
            utils.oauth_url(
                self.bot.user.id,
                permissions=Permissions(
                    read_messages=True,
                    send_messages=True,
                    add_reactions=True,
                    embed_links=True,
                    read_message_history=True,
                    manage_messages=True,
                ),
            )
        )

    @command()
    async def server(self, ctx: Context):
        """get a link to my server"""
        await ctx.send("https://discord.gg/aBM5xz6")

    @command()
    async def source(self, ctx: Context):
        """yes, I am open-souce"""
        await ctx.send("https://github.com/deadaf/whiskey")

    @command()
    async def stats(self, ctx: Context):
        await ctx.send(f"Servers: {len(self.bot.guilds)}\nUsers: {sum(g.member_count for g in self.bot.guilds)}")


def setup(bot):
    bot.add_cog(Utility(bot))
