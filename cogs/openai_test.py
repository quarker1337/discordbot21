import discord
from discord.ext import commands
from discord import ChannelType
import configparser
import os
import openai
import textwrap
import re

# Read the OpenAI API key from the configuration file
configfile = os.path.dirname(os.path.dirname(__file__)) + "\config.ini"
config = configparser.ConfigParser()
config.read(configfile)
openai.api_key = config['OpenAI']['TOKEN']

assistant = """
######
You are openai_test#2242, an assistant for Coders, Devops and Admins. 
Answer the Task/Question as helpful as possible and always try to provide Code, Script or Command Examples. 

If your Answer contains Code, Shellscripts, Scripts or Commands wrap them in the according Discord Markdown Format. When possible use Discords Markdown to highlight syntax.
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
            response_chunks = []
            code_block_matches = re.finditer("```[^```]*```", response)
            last_end = 0
            for match in code_block_matches:
                start, end = match.span()
                # Get the text before the code block
                before_block = response[last_end:start]
                # Wrap the text before the code block and add it to the list of chunks
                response_chunks.extend(textwrap.wrap(before_block, width=2000))
                # Add the code block as a separate chunk
                response_chunks.append(response[start:end])
                last_end = end

            # Handle the text after the last code block
            after_block = response[last_end:]
            response_chunks.extend(textwrap.wrap(after_block, width=2000))

            for chunk in response_chunks:
                await ctx.send(chunk)
        else:
            response = await generate_response(assistant + question + "\n'''")
            thread_name = question[:20]
            thread = await channel.create_thread(
                    name=thread_name,
                    type=ChannelType.public_thread
                )
            # Send the response to the channel where the command was called, split it up in several chunks if its longer then 2000 characters. Might break formatting.
            await thread.send(f"Your Question was: {question}")
            response_chunks = []
            code_block_matches = re.finditer("```[^```]*```", response)
            last_end = 0
            for match in code_block_matches:
                start, end = match.span()
                # Get the text before the code block
                before_block = response[last_end:start]
                # Wrap the text before the code block and add it to the list of chunks
                response_chunks.extend(textwrap.wrap(before_block, width=2000))
                # Add the code block as a separate chunk
                response_chunks.append(response[start:end])
                last_end = end

            # Handle the text after the last code block
            after_block = response[last_end:]
            response_chunks.extend(textwrap.wrap(after_block, width=2000))

            for chunk in response_chunks:
                await thread.send(chunk)


# Define an async function that uses the OpenAI API to generate a response
# to a given query
async def generate_response(query):
    # Use the OpenAI API to generate a response
    prompt = (f"{query}\n")
    completions = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1500,  # 2 * len(message.content),
        temperature=0.8,
        top_p=1,
        frequency_penalty=0.05,
        presence_penalty=0.001,
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
    print(response)
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