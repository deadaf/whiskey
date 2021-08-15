import asyncio
import discord
from discord.ext.commands.errors import CommandError


async def safe_delete(message) -> bool:
    try:
        await message.delete()
    except (discord.Forbidden, discord.NotFound):
        return False
    else:
        return True


async def string_input(ctx, check, timeout=120, delete_after=False) :
    try:
        message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        raise CommandError("Took too long. Good Bye.")
    else:
        if delete_after:
            await safe_delete(message)

        return message.content
