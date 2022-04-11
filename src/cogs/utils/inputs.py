from __future__ import annotations

import asyncio
from typing import Callable, Optional
import discord
from discord.ext import commands


async def safe_delete(message: discord.Message, *, timeout: float=0) -> None:
    await message.delete(delay=timeout)
    # this is hack, it internally ignores all the HTTP excpetions
    # if deleting messages fails


async def string_input(
    ctx: commands.Context, check: Callable, timeout: float=120, delete_after: bool=False
) -> Optional[str]:
    try:
        message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        raise commands.CommandError("Took too long. Good Bye.")
    else:
        if delete_after:
            await safe_delete(message)

        return message.content
