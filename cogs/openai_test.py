import discord
from discord.ext import commands
from discord import ChannelType
import configparser
import os
import openai

# Read the OpenAI API key from the configuration file
configfile = os.path.dirname(os.path.dirname(__file__)) + "\config.ini"
config = configparser.ConfigParser()
config.read(configfile)
openai.api_key = config['OpenAI']['TOKEN']

assistant = """
######
You are openai_test, an assistant for Coders, Devops and Admins. 
Answer the Task/Question as helpful as possible and always try to provide Code, Script or Command Examples.

If your Answer contains Code, Shellscripts, Scripts or Commands wrap them in the according Discord Markdown Format.
Always use proper Discord Format in your response.
'''
User:\n
"""

# Define a cog (a class that represents a group of commands and listeners)
# that has a command and an event listener
class gptbot_test(commands.Cog):
    def __init__(self, bot):
        # Initialize the cog with a reference to the bot
        self.bot = bot

    # Define a command that responds with "Pong" when called
    @commands.command(description="Opens a Thread or answers a Question in a Thread taking into Account the Thread History", brief="OpenAI with History")
    async def ai(self, ctx, *, question):
        channel = self.bot.get_channel(ctx.channel.id)
        moderator = await content_policy_check(ctx.message.content)
        if moderator == True:
            await ctx.send(f"This Question violates the OpenAI Content Policy.")
            return
        if ctx.channel.type in [ChannelType.public_thread, ChannelType.private_thread]:
            counter = 0
            output_lines = []
            counter = 0
            async for message in ctx.channel.history(limit=20):
                counter += 1
                output_lines.append(f"{counter}. {message.author}: {message.content}")
            output = "\n".join(output_lines[::-1])
            print(counter)
            print(output)
            response = await generate_response(assistant + output + question + "\n'''")
            print(response)
            await ctx.send(f"{response}")
        else:
            response = await generate_response(assistant + question + "\n'''")
            thread_name = question[:20]
            thread = await channel.create_thread(
                    name=thread_name,
                    type=ChannelType.public_thread
                )
            # Send the response to the channel where the command was called
            await thread.send(f"Your Question was: {question}")
            await thread.send(f"{ctx.message.author.mention} {response}")



# Define an async function that uses the OpenAI API to generate a response
# to a given query
async def generate_response(query):
    # Use the OpenAI API to generate a response
    prompt = (f"{query}\n")
    completions = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=2500,  # 2 * len(message.content),
        temperature=0.9,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    print(completions)
    message = completions["choices"][0]["text"]
    return message

# Define an async function that uses the OpenAI API to check if the OpenAI Content Policy is violated
# to a given query/question
async def content_policy_check(question):
    response = openai.Moderation.create(
        input=question,
    )
    if response["results"][0]["flagged"] == True:
        return True
    else:
        category_scores = response["results"][0]["category_scores"]
        for category, score in category_scores.items():
            if score > 0.4:
                return True
        else:
            return False

# Define an async function that adds the cog to the bot
async def setup(bot):
    await bot.add_cog(gptbot_test(bot))