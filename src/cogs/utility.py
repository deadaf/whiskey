from __future__ import annotations

import typing
import unicodedata

from constants import COLOR

if typing.TYPE_CHECKING:
    from bot import Whiskey

import re
import io
import os
import zlib
import discord

from .views import SelfRoles
from .utils import fuzzy
from discord.ext.commands import command, Context, Cog, group, is_owner


# https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/api.py


class SphinxObjectFileReader:
    # Inspired by Sphinx's InventoryFileReader
    BUFSIZE = 16 * 1024

    def __init__(self, buffer):
        self.stream = io.BytesIO(buffer)

    def readline(self):
        return self.stream.readline().decode("utf-8")

    def skipline(self):
        self.stream.readline()

    def read_compressed_chunks(self):
        decompressor = zlib.decompressobj()
        while True:
            chunk = self.stream.read(self.BUFSIZE)
            if len(chunk) == 0:
                break
            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def read_compressed_lines(self):
        buf = b""
        for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b"\n")
            while pos != -1:
                yield buf[:pos].decode("utf-8")
                buf = buf[pos + 1 :]
                pos = buf.find(b"\n")


class Utility(Cog):
    def __init__(self, bot: Whiskey):
        self.bot = bot

    def parse_object_inv(self, stream, url):
        # key: URL
        # n.b.: key doesn't have `discord` or `discord.ext.commands` namespaces
        result = {}

        # first line is version info
        inv_version = stream.readline().rstrip()

        if inv_version != "# Sphinx inventory version 2":
            raise RuntimeError("Invalid objects.inv file version.")

        # next line is "# Project: <name>"
        # then after that is "# Version: <version>"
        projname = stream.readline().rstrip()[11:]
        version = stream.readline().rstrip()[11:]

        # next line says if it's a zlib header
        line = stream.readline()
        if "zlib" not in line:
            raise RuntimeError("Invalid objects.inv file, not z-lib compatible.")

        # This code mostly comes from the Sphinx repository.
        entry_regex = re.compile(r"(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)")
        for line in stream.read_compressed_lines():
            match = entry_regex.match(line.rstrip())
            if not match:
                continue

            name, directive, prio, location, dispname = match.groups()
            domain, _, subdirective = directive.partition(":")
            if directive == "py:module" and name in result:
                # From the Sphinx Repository:
                # due to a bug in 1.1 and below,
                # two inventory entries are created
                # for Python modules, and the first
                # one is correct
                continue

            # Most documentation pages have a label
            if directive == "std:doc":
                subdirective = "label"

            if location.endswith("$"):
                location = location[:-1] + name

            key = name if dispname == "-" else dispname
            prefix = f"{subdirective}:" if domain == "std" else ""

            if projname == "discord.py":
                key = key.replace("discord.ext.commands.", "").replace("discord.", "")

            result[f"{prefix}{key}"] = os.path.join(url, location)

        return result

    async def build_rtfm_lookup_table(self, page_types):
        cache = {}
        for key, page in page_types.items():
            sub = cache[key] = {}
            async with self.bot.session.get(page + "/objects.inv") as resp:
                if resp.status != 200:
                    raise RuntimeError("Cannot build rtfm lookup table, try again later.")

                stream = SphinxObjectFileReader(await resp.read())
                cache[key] = self.parse_object_inv(stream, page)

        self._rtfm_cache = cache

    async def do_rtfm(self, ctx, key, obj):
        page_types = {
            "latest": "https://discordpy.readthedocs.io/en/latest",
            "python": "https://docs.python.org/3",
            "master": "https://discordpy.readthedocs.io/en/master",
        }

        if obj is None:
            await ctx.send(page_types[key])
            return

        if not hasattr(self, "_rtfm_cache"):
            await ctx.trigger_typing()
            await self.build_rtfm_lookup_table(page_types)

        obj = re.sub(r"^(?:discord\.(?:ext\.)?)?(?:commands\.)?(.+)", r"\1", obj)

        if key.startswith("latest"):
            # point the abc.Messageable types properly:
            q = obj.lower()
            for name in dir(discord.abc.Messageable):
                if name[0] == "_":
                    continue
                if q == name:
                    obj = f"abc.Messageable.{name}"
                    break

        cache = list(self._rtfm_cache[key].items())

        def transform(tup):
            return tup[0]

        matches = fuzzy.finder(obj, cache, key=lambda t: t[0], lazy=False)[:8]

        e = discord.Embed(colour=COLOR)
        if len(matches) == 0:
            return await ctx.send("Could not find anything. Sorry.")

        e.description = "\n".join(f"[`{key}`]({url})" for key, url in matches)
        await ctx.send(embed=e)

    @group(aliases=["rtfd"], invoke_without_command=True)
    async def rtfm(self, ctx, *, obj: str = None):
        """Gives you a documentation link for a discord.py entity.
        Events, objects, and functions are all supported through
        a cruddy fuzzy algorithm.
        """
        await self.do_rtfm(ctx, "latest", obj)

    @rtfm.command(name="python", aliases=["py"])
    async def rtfm_python(self, ctx, *, obj: str = None):
        """Gives you a documentation link for a Python entity."""
        await self.do_rtfm(ctx, "python", obj)

    @rtfm.command(name="master", aliases=["2.0"])
    async def rtfm_master(self, ctx, *, obj: str = None):
        """Gives you a documentation link for a discord.py entity (master branch)"""
        await self.do_rtfm(ctx, "master", obj)

    @command()
    async def invite(self, ctx: Context):
        """invite me"""
        await ctx.send(
            discord.utils.oauth_url(
                self.bot.user.id,
                permissions=discord.Permissions(
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
        await ctx.send("discord.gg/aBM5xz6")

    @command()
    async def source(self, ctx: Context):
        """yes, I am open-souce"""
        await ctx.send("<https://github.com/deadaf/whiskey>")

    @command()
    async def stats(self, ctx: Context):
        await ctx.send(f"Servers: {len(self.bot.guilds)}\nUsers: {sum(g.member_count for g in self.bot.guilds)}")

    @command()
    async def charinfo(self, ctx, *, characters: str):
        """
        Shows you information about a number of characters.
        Only up to 25 characters at a time.
        """

        def to_string(c):
            digit = f"{ord(c):x}"
            name = unicodedata.name(c, "Name not found.")
            return f"`\\U{digit:>08}`: {name} - {c} \N{EM DASH} <http://www.fileformat.info/info/unicode/char/{digit}>"

        msg = "\n".join(map(to_string, characters))
        if len(msg) > 2000:
            return await ctx.send("Output too long to display.")
        await ctx.send(msg)

    @command(hidden=True)
    @is_owner()
    async def selfroles(self, ctx):
        embed = discord.Embed(color=COLOR, title="Claim Self-Roles")
        embed.description = "Below is a list of self claimable roles along with the purpose they serve. We promise, we won't ping you unless it's really important."
        embed.add_field(
            name="**1. Quotient-Updates 🔔**",
            value="We will ping this role everytime we time we deploy an important update in <@746348747918934096>. *we try not to overdo it.*",
            inline=False,
        )
        embed.add_field(
            name="**2. Events(giveaways) 🎉**",
            value="This role will be mentioned when we host a new event or giveaway. (*giveaway most of the times*)",
            inline=False,
        )
        embed.add_field(
            name="**3. Black 🖊️**", value="Claim this if you want to look BLACK. (no racism pls)", inline=False
        )
        embed.add_field(
            name="**4. Discord Status 🍻**",
            value="Everytime discord gets drunk or shows unexpected behaviour, this role will be notified. (*we really recommend you to take this*)",
            inline=False,
        )
        await ctx.message.delete()
        await ctx.send(embed=embed, view=SelfRoles())


def setup(bot):
    bot.add_cog(Utility(bot))
