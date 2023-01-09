import discord
from discord.ext import commands

# Define a cog (a class that represents a group of commands and listeners)
# that has a command and an event listener
class ping(commands.Cog):
    def __init__(self, bot):
        # Initialize the cog with a reference to the bot
        self.bot = bot

    # Define an event listener that will be called when the bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is online")

    # Define a command that responds with "Pong" when called
    @commands.command(description="Answers with Pong", brief="Pong")
    async def ping(self, ctx):
        # Send a message to the channel where the command was called
        await ctx.send("Pong")

# Define an async function that adds the cog to the bot
async def setup(bot):
    await bot.add_cog(ping(bot))