from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from bot import Whiskey


from discord.ext.commands import command, Context, Cog
from discord import VoiceChannel, Forbidden, ClientException, utils, Permissions
from models import Voice
from contextlib import suppress


class Utility(Cog):
    def __init__(self, bot: Whiskey):
        self.bot = bot

    @command(name="24/7")
    async def vcjoin(self, ctx: Context, *, vc: VoiceChannel):
        """set a 24*7 vc channel"""
        await Voice.update_or_create(guild_id=ctx.guild.id, defaults={"voice_channel_id": vc.id})
        await ctx.send(f"Done. {vc.mention} is now a 24/7 vc.")

        with suppress(ClientException, Forbidden):
            await vc.connect()

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
                ),
            )
        )

    @command()
    async def server(self, ctx: Context):
        """get a link to my server"""
        await ctx.send("https://discord.gg/aBM5xz6")


def setup(bot):
    bot.add_cog(Utility(bot))
