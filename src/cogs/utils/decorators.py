from models import Response

from discord.ext import commands


def has_not_done_setup():
    async def predicate(ctx):
        record = await Response.get_or_none(guild_id=ctx.guild.id)
        if record:
            raise commands.CheckFailure(
                f"You have already done the auto-response setup.\n\nUse `{ctx.prefix}rcreate` to create a response."
            )

        return True

    return commands.check(predicate)


def has_done_setup():
    async def predicate(ctx):
        record = await Response.get_or_none(guild_id=ctx.guild.id)
        if not record:
            raise commands.CheckFailure(
                f"This server do not have auto-response setup.\n\nUse `{ctx.prefix}rsetup` to setup."
            )

        return True

    return commands.check(predicate)
