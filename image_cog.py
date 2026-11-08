"""All bot commands/events. Everything except !startscan/!stopscan is disabled until scanning is on."""
import discord
from discord.ext import commands

import config
import database as db
import scanner
import search
from tags import parse_tags


class ImageCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        if ctx.guild is None:
            return False
        if ctx.command.name in ("startscan", "stopscan"):
            return True
        return db.is_scan_enabled(ctx.guild.id)

    async def cog_command_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need the **Manage Server** permission to do that.")
        elif isinstance(error, commands.CheckFailure):
            if ctx.guild is not None:
                await ctx.send("Scanning is off. An admin can turn the bot on with `!startscan`.")
        else:
            print(f"Command error in {ctx.command}: {error}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None or not message.attachments:
            return
        if not db.is_scan_enabled(message.guild.id):
            return
        await scanner.scan_message(message)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def startscan(self, ctx: commands.Context):
        db.set_scan_enabled(ctx.guild.id, True)
        await ctx.send("Scanning started.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def stopscan(self, ctx: commands.Context):
        db.set_scan_enabled(ctx.guild.id, False)
        await ctx.send("Scanning stopped. All other commands are disabled until `!startscan`.")

    @commands.command()
    async def isalive(self, ctx: commands.Context):
        await ctx.send("I'm always searching for you!")

    @commands.command()
    async def searchimg(self, ctx: commands.Context, *, args: str):
        parts = args.split()
        limit = config.DEFAULT_RESULTS
        if parts and parts[0].isdigit():
            limit = max(1, min(int(parts[0]), config.MAX_RESULTS))
            parts = parts[1:]

        query_words = parse_tags(" ".join(parts))
        if not query_words:
            await ctx.send("Please provide search terms!")
            return

        async with ctx.typing():
            results = await search.find_images(ctx.guild.id, query_words, limit)

        if not results:
            await ctx.send(f"No matching images found for: `{' '.join(query_words)}`")
            return

        embeds = []
        for r in results:
            if r.exact_matches == r.total_words:
                title = f"Search Match ({r.exact_matches}/{r.total_words} tags)"
            else:
                title = f"Similar Match ({r.exact_matches}/{r.total_words} exact, rest similar)"
            embed = discord.Embed(title=title)
            embed.set_image(url=r.image_url)
            embed.description = (
                f"**Tags:** {r.description}\n*Posted by: {r.author}*\n\n"
                f"🔗 [Jump to Original Message]({r.jump_url})"
            )
            embeds.append(embed)

        try:
            await ctx.author.send(embeds=embeds)  # max 10 embeds per message
        except discord.Forbidden:
            await ctx.send(f"{ctx.author.mention} I can't DM you. Please enable DMs from server members.")
            return
    @commands.command
    async def h(self, ctx):
        await ctx.send("Basic usage:\n !startscan - start scanning\n!stopscan - stop scanning\nsearchimg <img amount> tags - search for images with tags, you can send text in the image or usernames as tags\n!isalive - Checks if the bot is alive(If you are seeing this then it is)")

        


async def setup(bot: commands.Bot):
    await bot.add_cog(ImageCog(bot))
