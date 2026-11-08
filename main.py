import asyncio
import os

import discord
from discord.ext import commands

import config

intents = discord.Intents.default()
intents.message_content = True


class ImageBot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("image_cog")


bot = ImageBot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot is logged in as {bot.user}")


if __name__ == "__main__":
    bot.run(config.TOKEN)
