from discord.ext import commands
from discord import app_commands
import discord
from lib.utils import (
    logger
)
from lib.sqlite import (
    load_db_user
)
class info(commands.Cog):
    def __init__(self, bot):
        # Initialize the cog with a reference to the bot
        self.bot = bot

    @app_commands.command(name="info", description="Gets User Information like Token Balance")
    @discord.app_commands.checks.has_permissions(send_messages=True)
    @discord.app_commands.checks.has_permissions(view_channel=True)
    @discord.app_commands.checks.bot_has_permissions(send_messages=True)
    @discord.app_commands.checks.bot_has_permissions(view_channel=True)
    @discord.app_commands.checks.bot_has_permissions(manage_threads=True)
    async def info(self, int: discord.Interaction) -> None:
        user = int.user
        db_user = await load_db_user(user)
        token_balance = db_user[2]
        lifetime_token_usage = db_user[3]
        usd = (lifetime_token_usage / 1000) * 0.02
        usd_formatted = "${:,.2f}".format(usd)
        embed = discord.Embed(
            description=f"Balance for User {user.name}",
            color=discord.Color.green(),
        )
        embed.add_field(name="Lifetime Token Usage:", value=lifetime_token_usage, inline=False)
        embed.add_field(name="Lifetime Costs:", value=usd_formatted, inline=False)
        embed.add_field(name="Tokens Left:", value=token_balance, inline=False)
        await int.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(info(bot))
