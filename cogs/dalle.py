import discord
from discord.ext import commands
import configparser
import os
import openai
import requests
import io

# Read the OpenAI API key from the configuration file
configfile = os.path.dirname(os.path.dirname(__file__)) + "\config.ini"
config = configparser.ConfigParser()
config.read(configfile)
openai.api_key = config['OpenAI']['TOKEN']

# Define a cog (a class that represents a group of commands and listeners)
# that has a command
class dalle(commands.Cog):
    def __init__(self, bot):
        # Initialize the cog with a reference to the bot
        self.bot = bot

    # Define a command that sends a question to the OpenAI API
    # and returns the response
    @commands.command(description="Use the !i command to send Requests to the Dall-E API to generate an Image", brief="Uses Dall-E to generate Images")
    async def i(self, ctx, *, question):
        # Call the 'generate_image' function to get a image from Dall-E
        try:
            image = await generate_image(question)
        except Exception as e:
            print(f"Error occurred when generating image: {e}")
            return

        # Send the response to the channel where the command was called
        # await ctx.send(response)
        image_file = discord.File(io.BytesIO(image), "dalle-image.png")
        await ctx.send(file=image_file)

# Define an async function that uses the OpenAI API to generate a response
# to a given query
async def generate_image(query):
    prompt = (f"{query}\n")
    r = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai.api_key}"
        },
        json={
            "model": "image-alpha-001",
            "prompt": prompt,
            "num_images": 1,
            "size": "1024x1024",
            "response_format": "url"
        }
    )
    image_url = r.json()["data"][0]["url"]

    # Download the image from the URL
    response = requests.get(image_url)
    image_data = response.content
    return image_data

# Define an async function that adds the cog to the bot
async def setup(bot):
    await bot.add_cog(dalle(bot))
