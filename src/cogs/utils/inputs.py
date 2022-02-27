from __future__ import annotations

import asyncio
import discord
from discord.ext.commands.errors import CommandError


async def safe_delete(message, *, timeout: float=0) -> bool:
    await message.delete(delay=timeout)
    # this is hack, it internally ignores all the HTTP excpetions
    # if deleting messages fails
    


async def string_input(ctx, check, timeout=120, delete_after=False):
    try:
        message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        raise CommandError("Took too long. Good Bye.")
    else:
        if delete_after:
            await safe_delete(message)

        return message.content
