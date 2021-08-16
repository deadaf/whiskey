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


def setup(bot):
    bot.add_cog(Utility(bot))
