from discord.ext import commands
from lib.utils import (
    logger,
    split_into_shorter_messages,
    fetch_system_channel
)
from lib.constants import (
    ADMINUSER,

)
from lib.weaviate import (
    createschema,
    countobjects,
    listobjects,
    listnearobjects,
    deleteobject,
)
from lib.sqlite import (
    create_database,
    get_db_users,
    update_balance,
    get_db_prompts,
)

# Define a cog (a class that represents a group of commands and listeners)
# that has a command and an event listener
class db(commands.Cog):
    def __init__(self, bot):
        # Initialize the cog with a reference to the bot
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        logger.info(f"Message_ID: {message.id} Author: {message.author.id} Content: {message.content}")

    @commands.has_permissions(administrator=True)
    @commands.command(description="does things", brief="does things")
    async def db(self, ctx, command=None, arg1=None, arg2=None, arg3=None):
        # We don't want these commands to run in anything but SYSTEMCHANNELS
        SYSCHANNELS = await fetch_system_channel(ctx.guild)
        if ctx.channel.id != SYSCHANNELS.id:
            return
        # Only the Bot-Owner/Operator should be allow to use the DB Commands
        if ctx.message.author.id != ADMINUSER:
            await ctx.send(f"Not authorized to use Command. Check Documentation.")
            return
        else:
            if command is None:
                await ctx.send(f"Valid Commands are createschema, listobjects, listnearobjects, deleteobjects, sqlite createuserdb, sqlite listusers")
            elif command == "createschema":
                await createschema()
            elif command == "listobjects":
                if arg1 is not None:
                    count = await countobjects(arg1)
                    results = await listobjects(arg1)
                    result_list = [[message["_additional"]["id"], message["content"]] for message in results["data"]["Get"][f"{arg1}"]]
                    await ctx.send(f"```{count}```")
                    for message in result_list:
                        shorter_response = split_into_shorter_messages(message[1])
                        await ctx.send(f">>> *Object*: {arg1} ")
                        await ctx.send(f">>> *ID*: {message[0]}")
                        await ctx.send(f">>> *Content*:")
                        for r in shorter_response:
                            await ctx.send(f">>> {r}")
            elif command == "listnearobjects":
                if arg2 is not None:
                    results = await listnearobjects(arg1, arg2)
                    result_list = [[message["_additional"]["id"], message["content"]] for message in results["data"]["Get"][f"{arg1}"]]
                    await ctx.send(f"Objects for Class: {arg1} with nearText: {arg2}")
                    for message in result_list:
                        shorter_response = split_into_shorter_messages(message[1])
                        await ctx.send(f">>> *Object*: {arg1} ")
                        await ctx.send(f">>> *ID*: {message[0]}")
                        await ctx.send(f">>> *Content*:")
                        for r in shorter_response:
                            await ctx.send(f">>> {r}")
            elif command == "deleteobjects":
                if arg2 is not None:
                    result = await deleteobject(arg1, arg2)
                    await ctx.send(f"Deleted Object Result: {result}")
            elif command == "sqlite":
                if arg1 == "createuserdb":
                    conn = await create_database()
                    await ctx.send(f"Created SQL-Lite DB for Users: {conn}")
                if arg1 == "listusers":
                    users = get_db_users()
                    for user in users:
                        id = user[0]
                        username = user[1]
                        tokens = user[2]
                        lifetimetokens = user[3]
                        message = f"ID: {id}\nUsername: {username}\nTokens: {tokens}\nLifetime Tokens: {lifetimetokens}"
                        await ctx.send(message)
                    return
                if arg1 == "listprompts":
                    prompts = await get_db_prompts()
                    await ctx.send(f">>> Listing Prompts and Completions.")
                    for prompt in prompts:
                        type = prompt[0]
                        input = prompt[1]
                        completion = prompt[2]
                        message = f">>> Type: {type}\nPrompt: {input}\nCompletion: {completion}"
                        await ctx.send(message)
                    return
                if arg1 == "updatebalance":
                    if arg2 and arg3 is not None:
                        user = await self.bot.fetch_user(arg2)
                        result, old_tokens = await update_balance(user, int(arg3))
                        await ctx.send(f">>> User: {user.name}")
                        await ctx.send(f">>> Old Token Amount: {old_tokens} ")
                        await ctx.send(f">>> New Token Amount: {result[2]} ")
# Define an async function that adds the cog to the bot
async def setup(bot):
    await bot.add_cog(db(bot))