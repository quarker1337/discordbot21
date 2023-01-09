from discord.ext import commands
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
Below is a Task from a User on a Discord Chatchannel.
If your Answer contains Code, Shellscripts, Scripts or Commands wrap them in the according Discord Markdown Format.
If your Answer contains Lyrics, Receipes, Poems or other Big Content use Discord Formatting as well. 

'''
User:\n
"""

dota = """--- You are a coach for Dota 2 and a player asks you the following question, how do you answer?: --- '''"""

# Define a cog (a class that represents a group of commands and listeners)
# that has a command
class gptbot(commands.Cog):
    def __init__(self, bot):
        # Initialize the cog with a reference to the bot
        self.bot = bot

    # Define a command that sends a question to the OpenAI API
    # and returns the response
    @commands.command(description="Use the !ask command to send Questions to the OpenAI API", brief="Uses OpenAI to complete Text")
    async def a(self, ctx, *, question):
        moderator = await content_policy_check(ctx.message.content)
        if moderator == True:
            await ctx.send(f"This Question violates the OpenAI Content Policy.")
            return
        # Call the 'generate_response' function to get a response from the OpenAI API
        response = await generate_response(question)
        # Print the chat log
        print("Chatlog_OpenAI:", ctx.message.author, ":", "Question:", question, "Response:", response)
        # Send the response to the channel where the command was called
        await ctx.send(f"{ctx.message.author.mention} {response}")

    # Define a command that sends a question to the OpenAI API
    # and returns the response
    @commands.command(description="Use the !ask_assistant command to send Questions to the OpenAI API and get proper Answers in Discord Markdown", brief="Uses OpenAI to complete Tasks and format the Output")
    async def aa(self, ctx, *, question):
        moderator = await content_policy_check(ctx.message.content)
        if moderator == True:
            await ctx.send(f"This Question violates the OpenAI Content Policy.")
            return
        # Call the 'generate_response' function to get a response from the OpenAI API
        response = await generate_response(assistant + question +"\n'''")
        # Print the chat log
        print("Chatlog_OpenAI:", ctx.message.author, ":", "Question:", question, "Response:", response)
        # Send the response to the channel where the command was called
        await ctx.send(f"{ctx.message.author.mention} {response}")

    # Define a command that sends a question to the OpenAI API
    # and returns the response
    @commands.command(description="Use the !ask_dota command to send Dota Questions to the OpenAI API",
                      brief="Uses OpenAI to answer Dota specific Questions")
    async def ad(self, ctx, *, question):
        moderator = await content_policy_check(ctx.message.content)
        if moderator == True:
            await ctx.send(f"This Question violates the OpenAI Content Policy.")
            return
        # Call the 'generate_response' function to get a response from the OpenAI API
        response = await generate_response(dota + question + "\n'''")
        # Print the chat log
        print("Chatlog_OpenAI:", ctx.message.author, ":", "Question:", question, "Response:", response)
        # Send the response to the channel where the command was called
        await ctx.send(f"{ctx.message.author.mention} {response}")


# Define an async function that uses the OpenAI API to generate a response
# to a given query
async def generate_response(query):
    # Use the OpenAI API to generate a response
    prompt = (f"{query}\n")
    completions = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=2500,  # 2 * len(message.content),
        temperature=0,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
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
            if score > 0.8:
                return True
        else:
            return False

# Define an async function that adds the cog to the bot
async def setup(bot):
    await bot.add_cog(gptbot(bot))