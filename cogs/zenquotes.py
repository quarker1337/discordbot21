import discord
from discord.ext import commands
import requests
import json

class quote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #@commands.Cog.listener()

    @commands.command(description="Answers with a Random Quote from https://zenquotes.io/api/random", brief="Gets a Random Quote from Zenquotes")
    async def quote(self, ctx):
        response = requests.get("https://zenquotes.io/api/random")
        json_data = json.loads(response.text)
        quote = json_data[0]['q'] + " -" + json_data[0]['a']
        await ctx.send(quote)

async def setup(bot):
    await bot.add_cog(quote(bot))