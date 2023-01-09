from discord.ext import commands
import configparser
import os
import openai
import glob

# Read the OpenAI API key from the configuration file
configfile = os.path.dirname(os.path.dirname(__file__)) + "\config.ini"
config = configparser.ConfigParser()
config.read(configfile)
openai.api_key = config['OpenAI']['TOKEN']

# Read all txt files in the "prompt" directory
prompt_files = glob.glob("prompt/*.txt")
print(prompt_files)
prompts = {}

for file in prompt_files:
    with open(file, 'r') as f:
        prompts[os.path.basename(file).split('.txt')[0]] = f.read()

print(prompts)
# Define a cog (a class that represents a group of commands and listeners)
# that has a command
class gptbot_blub(commands.Cog):
    def __init__(self, bot):
        # Initialize the cog with a reference to the bot
        self.bot = bot

    # Define a command that sends a question to the OpenAI API
    # and returns the response
    @commands.command(description="Use the !ask command to send Questions to the OpenAI API",
                      brief="Uses OpenAI to complete Text")
    async def ask(self, ctx, prompt: str, *, question):
        print(ctx.message.content)
        moderator = await content_policy_check(ctx.message.content)
        if moderator == True:
            await ctx.send(f"This Question violates the OpenAI Content Policy.")
            return
        if prompt not in prompts:
            await ctx.send(
                f"Invalid prompt. Please choose a valid prompt from the following list: {', '.join(prompts.keys())}")
            return
        # Call the 'generate_response' function to get a response from the OpenAI API
        response = await generate_response(prompts[prompt] + question + "\n'''")
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
        temperature=0.9,
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
    await bot.add_cog(gptbot_blub(bot))