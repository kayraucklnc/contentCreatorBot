from http import client
import discord
from discord.ext import commands
import os
import asyncio

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())


@client.command()
async def load(ctx, extension):
    client.load_extension(f"cogs.{extension}")


@client.command()
async def unload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")


async def load_extensions():
    for filename in os.listdir("scripts/cogs"):
        if filename.endswith(".py"):
            # cut off the .py from the file name
            await client.load_extension(f"cogs.{filename[:-3]}")


async def main():
    async with client:
        await load_extensions()
        await client.start('')


asyncio.run(main())
