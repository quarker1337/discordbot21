from lib.constants import (
    ALLOWED_SERVER_IDS,
)
import logging
logger = logging.getLogger(__name__)
from lib.base import Message
from discord import Message as DiscordMessage
from typing import Optional, List
import discord

from lib.constants import MAX_CHARS_PER_REPLY_MSG, INACTIVATE_THREAD_PREFIX, SERVER_TO_SYSTEMCHANNEL


def discord_message_to_message(message: DiscordMessage) -> Optional[Message]:
    if (
        message.type == discord.MessageType.thread_starter_message
        and message.reference.cached_message
        and len(message.reference.cached_message.embeds) > 0
        and len(message.reference.cached_message.embeds[0].fields) > 0
    ):
        field = message.reference.cached_message.embeds[0].fields[0]
        if field.value:
            return Message(user=field.name, text=field.value)
    else:
        if message.content:
            return Message(user=message.author.name, text=message.content)
    return None


def split_into_shorter_messages(message: str) -> List[str]:
    return [
        message[i : i + MAX_CHARS_PER_REPLY_MSG]
        for i in range(0, len(message), MAX_CHARS_PER_REPLY_MSG)
    ]

async def fetch_system_channel(
    guild: Optional[discord.Guild],
) -> Optional[discord.abc.GuildChannel]:
    if not guild or not guild.id:
        return None
    moderation_channel = SERVER_TO_SYSTEMCHANNEL.get(guild.id, None)
    if moderation_channel:
        channel = await guild.fetch_channel(moderation_channel)
        return channel
    return None

async def send_usage(
    guild: Optional[discord.Guild],
    user: str,
    tokens: int,
    url: str
):
    usd = (tokens/1000) * 0.02
    usd_formatted = "${:,.2f}".format(usd)
    statuschannel = await fetch_system_channel(guild=guild)

    embed = discord.Embed(title=url, description="\n", color=0x00ff00)
    embed.add_field(name="User", value=user, inline=True)
    embed.add_field(name="Tokens", value=tokens, inline=True)
    embed.add_field(name="Costs", value=usd_formatted, inline=True)
    await statuschannel.send(embed=embed)

def is_last_message_stale(
    interaction_message: DiscordMessage, last_message: DiscordMessage, bot_id: str
) -> bool:
    return (
        last_message
        and last_message.id != interaction_message.id
        and last_message.author
        and last_message.author.id != bot_id
    )


async def close_thread(thread: discord.Thread):
    await thread.edit(name=INACTIVATE_THREAD_PREFIX)
    await thread.send(
        embed=discord.Embed(
            description="**Thread closed** - Context limit reached, closing...",
            color=discord.Color.blue(),
        )
    )
    await thread.edit(archived=True, locked=True)


def should_block(guild: Optional[discord.Guild]) -> bool:
    if guild is None:
        # dm's not supported
        logger.info(f"DM not supported")
        return True

    if guild.id and guild.id not in ALLOWED_SERVER_IDS:
        # not allowed in this server
        logger.info(f"Guild {guild} not allowed")
        return True
    return False