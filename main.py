import asyncio
import os
import discord
from discord.ext import commands
import configparser

# Read the bot's configuration from a file called 'config.ini'
config = configparser.ConfigParser()
config.read('config.ini')

# Create a 'discord.Intents' object with all available intents enabled
# and then enable membership intent as well
intents = discord.Intents.all()
intents.members = True

# Initialize a 'commands.Bot' object with a command prefix of "!"
# and the defined intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Read the Discord API token from the configuration file
discord_token = config['DISCORD']['TOKEN']

# Define an async function that loads all extensions (Python files)
# in the 'cogs' directory that have the '.py' extension
async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

# Define an async function that runs the 'load' function and then
# starts the bot using the 'discord_token'
async def main():
    await load()
    await bot.start(discord_token)

# Run the 'main' function asynchronously
asyncio.run(main())