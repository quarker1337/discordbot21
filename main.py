import asyncio
import os
import discord
from discord.ext import commands
import configparser
import logging
from lib.utils import (
        logger,
)
import openai
#format="[%(asctime)s] [%(filename)s:%(lineno)d] %(message)s"
logging.basicConfig(filename='example.log', encoding='utf-8', format="[%(asctime)s] %(message)s", level=logging.INFO)


# Read the bot's configuration from a file called 'config.ini'
config = configparser.ConfigParser()
config.read('config.ini')

# Create a 'discord.Intents' object with all available intents enabled
# and then enable membership intent as well
intents = discord.Intents.all()
intents.members = True

# Initialize a 'commands.Bot' object with a command prefix of "!"
# and the defined intents
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Read the Discord API token from the configuration file
discord_token = config['DISCORD']['TOKEN']
openai.api_key = config['OpenAI']['TOKEN']
#models = openai.Model.list()
#print(models)

# Define an async function that loads all extensions (Python files)
# in the 'cogs' directory that have the '.py' extension
async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            extension = f'cogs.{filename[:-3]}'
            logger.info(f'Loading extension {extension}...')
            await bot.load_extension(extension)
    logger.info("All the cogs are Loaded")

# Define an async function that runs the 'load' function and then
# starts the bot using the 'discord_token'
async def main():
    await load()
    await bot.start(discord_token)

# Run the 'main' function asynchronously
asyncio.run(main())