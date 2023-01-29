from discord.ext import commands
import json
import spacy
import pytextrank
import textwrap
import re
from lib.utils import (
    logger,
)
from lib.constants import (
    WEAVICLIENT,
    ADMINUSER,
    IGNORECHANNEL,
    EXAMPLESCHANNEL,
)

client = WEAVICLIENT

# Define a cog (a class that represents a group of commands and listeners)
# that has a command and an event listener
class db(commands.Cog):
    def __init__(self, bot):
        # Initialize the cog with a reference to the bot
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        logger.info(f"Message_ID: {message.id} Author: {message.author.id} Content: {message.content}")
        """
        # This Saves basically every Message outside of some Channels:
        if message.channel.id not in IGNORECHANNEL:
            if message.author.id == ADMINUSER:
                message_obj = {
                    "messageID": message.id,
                    "content": message.content,
                }
                print(message_obj)

                client.data_object.create(
                    data_object = message_obj,
                    class_name = "Messages",
                )
        """
        # Function to Save Messages in Example Conversation
        if message.channel.id in EXAMPLESCHANNEL:
            if message.author.id == ADMINUSER:
                example_obj = {
                    "messageID": message.id,
                    "content": message.content,
                }
                print(example_obj)

                client.data_object.create(
                    data_object= example_obj,
                    class_name= "Examples"
                )
                logger.info(f"Written new Examples Object with ID {message.id}")

    # Define the DB Commmand
    @commands.has_permissions(administrator=True)
    @commands.command(description="does things", brief="does things")
    async def dbobjects(self, ctx, prompt=None):
        if ctx.message.author.id == ADMINUSER:
            if prompt is None:
                messages = listmessages()
                testresult = (
                    client.query
                    .aggregate('Messages')
                    .with_meta_count()
                    .do()
                )
                await ctx.send(f"```{testresult}```")
                result_list = [[message["messageID"], message["content"]] for message in
                                messages["data"]["Get"]["Messages"]]
                for message in result_list:
                    await ctx.send(f">>> **Messages:** {message[1]}")
            else:
                outputN = listnear(prompt)
                output = listnearsummarized(prompt)
                result_list = [[message["messageID"], message["_additional"]["summary"][0]["result"]] for message in
                               output["data"]["Get"]["Messages"]]

                resultN_list = [[message["messageID"], message["content"]] for message in
                                outputN["data"]["Get"]["Messages"]]

                for message in result_list:
                    await ctx.send(f">>> **Messageid:** {message[0]} \n **Summary:** {message[1]}")
                for message in resultN_list:
                    await ctx.send(f">>> **Messageid:** {message[0]} \n **Content:** {message[1]}")
        else:
            await ctx.send("Not authorized to use commmand")

    @commands.has_permissions(administrator=True)
    @commands.command(description="does things", brief="does things")
    async def dbexamples(self, ctx, prompt=None):
        if ctx.message.author.id == ADMINUSER:
            if prompt is None:
                examples = listexamples()
                testresult = (
                    client.query
                    .aggregate('Examples')
                    .with_meta_count()
                    .do()
                )
                await ctx.send(f"```{testresult}```")
                await ctx.send(f">>> **Examples:** {examples}")
            else:
                outputN = listnearexamples(prompt)
                resultN_list = [[message["messageID"], message["content"]] for message in
                                outputN["data"]["Get"]["Examples"]]
                for message in resultN_list:
                    await ctx.send(f">>> Example Conversation:")
                    await ctx.send(f">>> **Messageid:** {message[0]} \n **Content:** {message[1]}")
        else:
            await ctx.send("Not authorized to use commmand")

    @commands.has_permissions(administrator=True)
    @commands.command(description="does things", brief="does things")
    async def dbmemorys(self, ctx, prompt=None):
        if ctx.message.author.id == ADMINUSER:
            if prompt is None:
                memorys = listmemorys()
                testresult = (
                    client.query
                    .aggregate('Memorys')
                    .with_meta_count()
                    .do()
                )
                await ctx.send(f"```{testresult}```")
                await ctx.send(f">>> **Memorys:** {memorys}")
            else:
                outputN = listnearmemorys(prompt)
                resultN_list = [[message["title"], message["content"]] for message in
                                outputN["data"]["Get"]["Memorys"]]
                for message in resultN_list:
                    await ctx.send(f">>> Memorys:")
                    await ctx.send(f">>> **Title:** {message[0]} \n **Content:** {message[1]}")
        else:
            await ctx.send("Not authorized to use commmand")

    @commands.has_permissions(administrator=True)
    @commands.command(description="does things", brief="does things")
    async def db(self, ctx, prompt: str):
        # only let me run this command
        if ctx.message.author.id == ADMINUSER:
            if prompt == "createschema":
                await createschema()
            elif prompt == "delete":
                # delete all classes
                client.schema.delete_all()
            else:
            # Send a message to the channel where the command was called
                schema = client.schema.get()
                output = craftresponse(json.dumps(schema, indent=4))
                print("output:", output)
                for chunk in output:
                    await ctx.send(f"```{chunk}```")
        else:
            await ctx.send("Not authorized to use commmand")

    @commands.has_permissions(administrator=True)
    @commands.command(description="does things", brief="does things")
    async def spacy(self, ctx, prompt=None):
        if ctx.message.author.id != ADMINUSER:
            await ctx.send("Not authorized to use commmand")
            return
        else:
            if prompt == None:
                await ctx.send("Send Question")
            else:
                # Load the spaCy model
                nlp = spacy.load("en_core_web_lg")
                nlp.add_pipe("textrank")
                message = prompt
                doc = nlp(message)

                # Extract keywords
                keywords = [token.text for token in doc if not token.is_stop]
                print("Keywords:", keywords)
                await ctx.send(f"```{keywords}```")

                # Extract entities
                entities = [ent.text for ent in doc.ents]
                print("Entities:", entities)
                await ctx.send(f"```{entities}```")

                for phrase in doc._.phrases:
                    await ctx.send(f"```Text: {phrase.text} Rank: {phrase.rank} Count: {phrase.count}```")
                    print(phrase.text)
                    print(phrase.rank, phrase.count)
                    print(phrase.chunks)



# New Schema Create Function, this only needs to run once!
def createschema():
    # Creating Basic Schema that we need to save Example Conversations
    memory_class_obj = {
        "class": "Memorys",
        "description": "Example Conversations",
        "properties": [
            {
                "dataType": [
                    "string"
                ],
                "description": "Title of Memory",
                "name": "Title"
            },
            {
                "dataType": [
                    "string"
                ],
                "description": "Memory Content",
                "name": "Content"
            }
        ]
    }
    example_class_obj = {
        "class": "Examples",
        "description": "Example Conversations",
        "properties": [
            {
                "dataType": [
                    "number"
                ],
                "description": "messageID",
                "name": "messageID"
            },
            {
                "dataType": [
                    "string"
                ],
                "description": "Example Conversation",
                "name": "Content"
            }
        ]

    }
    web_summarys_class_obj = {
        "class": "WebExtract",
        "description": "Website Text Extractions",
        "properties": [
            {
                "dataType": [
                    "number"
                ],
                "description": "messageID",
                "name": "messageID"
            },
            {
                "dataType": [
                    "string"
                ],
                "description": "Raw Content that got extracted",
                "name": "raw",
                "moduleConfig": {
                    "text2vec-transformers": {
                        "vectorizePropertyName": "false",
                        "skip": "true"
                        }
                }
            },
            {
                "dataType": [
                    "string"
                ],
                "description": "Fact List",
                "name": "facts"
            }
        ]

    }
    server_class_obj = {
        "class": "Server",
        "description": "Discord Servers",
        "properties": [
            {
                "dataType": [
                    "number"
                ],
                "description": "Discord Unique ID of the Channel",
                "name": "ServerID"
            },
            {
                "dataType": [
                    "string"
                ],
                "description": "Servername in Discord",
                "name": "server_name"
            }
        ]

    }
    channel_class_obj = {
        "class": "Channel",
        "description": "Discord Channels",
        "properties": [
            {
                "dataType": [
                    "number"
                ],
                "description": "Discord Unique ID of the Channel",
                "name": "ChannelID"
            },
            {
                "dataType": [
                    "string"
                ],
                "description": "Channelname in Discord",
                "name": "channel_name"
            }
        ]

    }
    users_class_obj = {
        "class": "User",
        "description": "Authors of Discord Messages",
        "properties": [
            {
                "dataType": [
                    "number"
                ],
                "description": "Discord Unique ID of the User",
                "name": "UserID"
            },
            {
                "dataType": [
                    "string"
                ],
                "description": "The Username of the User",
                "name": "Username"
            },
            {
                "dataType": [
                    "string"
                ],
                "description": "The nick of the User",
                "name": "Nick"
            }
        ]
    }

    messages_class_obj = {
        "class": "Messages",
        "description": "Discord Messages",
                       "properties": [
        {
            "dataType": [
                "number"
            ],
            "description": "Discord Unique ID of the Message",
            "name": "MessageID"
        },
        {
            "dataType": [
                "string"
            ],
            "description": "The Message content",
            "name": "Content"
        }
    ]
}
    client.schema.create_class(example_class_obj)
    client.schema.create_class(server_class_obj)
    client.schema.create_class(channel_class_obj)
    client.schema.create_class(users_class_obj)
    client.schema.create_class(messages_class_obj)
    client.schema.create_class(web_summarys_class_obj)
    client.schema.create_class(memory_class_obj)
# Create Cross-References


# Function to list all Messages Objects in Weaviate
def listmessages():
    query = """
    {
        Get {
         Messages(
            limit: 3
            sort: [{
                path: ["_lastUpdateTimeUnix"]
                order: desc
                }]
          ){
         messageID
         content
         }
        }
    }
    """
    result= client.query.raw(query)
    return result


def listexamples():
    query = """
    {
        Get {
         Examples(
            limit: 3
            sort: [{
                path: ["_lastUpdateTimeUnix"]
                order: desc
                }]
          ){
         messageID
         content
         }
        }
    }
    """
    result= client.query.raw(query)
    return result

def listmemorys():
    query = """
    {
        Get {
         Memorys(
            limit: 3
            sort: [{
                path: ["_lastUpdateTimeUnix"]
                order: desc
                }]
          ){
         title
         content
         }
        }
    }
    """
    result= client.query.raw(query)
    return result

def listnearsummarized(question):
    nearText = {
        "concepts": [question],
        "distance": 0.7,  # prior to v1.14 use "certainty" instead of "distance"
    }
    result = (
        client.query
        .get('Messages', ['messageID', '_additional {summary ( properties: ["content"]) { property result }}'])
        .with_near_text(nearText)
        .with_limit(3)
        .do()
    )

    print(result)
    return result

def listnear(question):
    nearText = {
        "concepts": [question],
        "distance": 0.7,  # prior to v1.14 use "certainty" instead of "distance"
    }
    result = (
        client.query
        .get('Messages', ['messageID', 'content'])
        .with_near_text(nearText)
        .with_limit(3)
        .do()
    )

    print(result)
    return result

def listnearmemorys(question):
    nearText = {
        "concepts": [question],
        "distance": 0.7,  # prior to v1.14 use "certainty" instead of "distance"
    }
    result = (
        client.query
        .get('Memorys', ['title', 'content'])
        .with_near_text(nearText)
        .with_limit(5)
        .do()
    )

    print(result)
    return result

def listnearexamples(question):
    print("trying to find near message example")
    nearText = {
        "concepts": [question],
        "distance": 0.7,  # prior to v1.14 use "certainty" instead of "distance"
    }
    result = (
        client.query
        .get('Examples', ['messageID', 'content'])
        .with_near_text(nearText)
        .with_limit(3)
        .do()
    )

    print(result)
    return result

# Function to split up to long responses
def craftresponse(input):
    response_chunks = []
    code_block_matches = re.finditer("```[^```]*```", input)
    last_end = 0
    for match in code_block_matches:
        start, end = match.span()
        # Get the text before the code block
        before_block = input[last_end:start]
        # Wrap the text before the code block and add it to the list of chunks
        response_chunks.extend(textwrap.wrap(before_block, width=2000))
        # Add the code block as a separate chunk
        response_chunks.append(response[start:end])
        last_end = end

    # Handle the text after the last code block
    after_block = input[last_end:]
    response_chunks.extend(textwrap.wrap(after_block, width=2000))
    return response_chunks

# Define an async function that adds the cog to the bot
async def setup(bot):
    await bot.add_cog(db(bot))