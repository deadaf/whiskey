from __future__ import annotations

from difflib import get_close_matches
from typing import Optional
from discord.ext import commands
from constants import COLOR
import discord


class HelpCommand(commands.HelpCommand):
    def __init__(self) -> None:
        super().__init__(
            command_attrs={
                "help": "Shows help about the bot, a command, or a category",
            },
            verify_checks=False,
        )

    async def send_bot_help(self, mapping) -> Optional[discord.Message]:
        ctx = self.context
        cats = []

        for cog, cmds in mapping.items():
            if cog and await self.filter_commands(cmds, sort=True):
                cats.append(cog)

        embed = discord.Embed(color=discord.Color(COLOR))
        for idx in cats:
            embed.add_field(
                inline=False,
                name=idx.qualified_name.title(),
                value=", ".join(map(lambda x: f"`{x}`", filter(lambda x: not x.hidden, idx.get_commands()))),
            )

        embed.set_footer(text="discord.gg/quotient")
        return await ctx.send(embed=embed)

    async def command_not_found(self, string: str) -> str:
        message = f"Could not find the `{string}` command. "
        commands_list = [str(cmd) for cmd in self.context.bot.walk_commands()]

        if dym := "\n".join(get_close_matches(string, commands_list)):
            message += f"Did you mean...\n{dym}"

        return message

    async def send_command_help(self, command) -> Optional[discord.Message]:
        embed = self.common_command_formatting(command)
        return await self.context.send(embed=embed)

    def common_command_formatting(self, command) -> discord.Embed:
        embed = discord.Embed(color=COLOR)
        embed.title = command.qualified_name

        if command.description:
            embed.description = f"{command.description}\n\n{command.help}"
        else:
            embed.description = command.help or "No help found..."
        embed.add_field(name="**Usage** ", value=f"`{self.get_command_signature(command)}`")

        return embed
