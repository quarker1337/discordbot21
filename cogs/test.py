import discord
from discord.ext import commands

class test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="Responds with the Message send by User", brief="Just a Test")
    async def test(self, ctx):
        await ctx.send(ctx.message.content)

async def setup(bot):
    await bot.add_cog(test(bot))