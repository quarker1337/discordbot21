from enum import Enum
import datetime
import dacite
import yaml
import asyncio
from dataclasses import dataclass
from transformers import GPT2Tokenizer
import openai
from lib.moderation import moderate_message
from typing import Optional, List
from lib.websearch import websearch
from lib.constants import (
    BOT_INSTRUCTIONS,
    BOT_NAME,
    WEAVICLIENT,
    EXAMPLE_CONVOS,
    QUERY_INSTRUCTIONS,
    QUERY_EXAMPLES,
    ENCODER_EXAMPLES,
    ENCODER_INSTRUCTIONS,
    DECODER_INSTRUCTIONS,
    DECODER_EXAMPLES
)
import discord
from lib.base import Message, Prompt, Conversation, Config, QueryPrompt, Websearch, Memory
from lib.utils import split_into_shorter_messages, close_thread, logger, send_usage
from lib.moderation import (
    send_moderation_flagged_message,
    send_moderation_blocked_message,
)
from lib.sqlite import (
    update_token_usage,
    save_prompt_db
)
MY_BOT_EXAMPLE_CONVOS = EXAMPLE_CONVOS
MY_BOT_NAME = BOT_NAME
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
client = WEAVICLIENT

class CompletionResult(Enum):
    OK = 0
    TOO_LONG = 1
    INVALID_REQUEST = 2
    OTHER_ERROR = 3
    MODERATION_FLAGGED = 4
    MODERATION_BLOCKED = 5


@dataclass
class CompletionData:
    status: CompletionResult
    reply_text: Optional[str]
    status_text: Optional[str]
    tokens: Optional[int]



## Decision Routine
async def querygenerator(messages: List[Message]):
    #### Time to build a Custom Prompt to ask GPT3 what Searchterms could be used to gather Information about our last message.
    EXAMPLES = []
    messages = messages[-5:]
    for c in QUERY_EXAMPLES:
        example_messages = []
        for m in c.messages:
            if m.user == "Lenard":
                example_messages.append(Message(user=MY_BOT_NAME, text=m.text))
            else:
                example_messages.append(m)
        EXAMPLES.append(Conversation(messages=example_messages))
    querygenerator = QueryPrompt(
        header=Message(
            "System", f"Instructions for {MY_BOT_NAME}: {QUERY_INSTRUCTIONS}"
        ),
        examples=EXAMPLES,
        convo=Conversation(messages + [Message("Querygenerator")]),
    )
    rendered = querygenerator.render()
    ##### TIME TO BUILD SOME SEARCHTERMS

    response = await openai.Completion.acreate(
        engine="text-davinci-003",
        prompt=rendered,
        temperature=0,
        top_p=0.9,
        max_tokens=512,
        stop=["||>"],
    )
    #logger.info(f"DEBUG OPENAI Query ANSWER: {response}")
    ##### Now we have a String in Semilist format and need to decide some stuff we do with it
    ##### First lets create a proper List Object out of it
    text = response["choices"][0]["text"]
    await save_prompt_db("query", messages[-1].text, text)
    # Split the text by "|"
    text_list = text.split("|")

    # Initialize the two lists
    msg_category = ""
    msg_searchterms = []

    # Get the category from the first item
    msg_category = text_list[0].strip()

    # Get the search terms from the second item
    msg_searchterms = text_list[1].strip().split(",")

    # Remove any leading or trailing whitespaces
    msg_searchterms = [x.strip() for x in msg_searchterms]

    # Print the lists to check the results
    logger.info(f"Querygenerator: msg_category: {msg_category} msg_searchterms: {msg_searchterms}")
    ##### Now we can return these things to our Decision Engine
    ##### msg_category, msg_searchterms, response.usage.total_token
    return msg_category, msg_searchterms, response.usage.total_tokens

async def decoder(messages: List[Message], Context):
    if len(messages) > 2:
        modmessages = [messages[0], messages[-1]]
        messages = messages[::-1]
        current_tokens = sum(len(tokenizer.tokenize(m.text)) for m in modmessages)
        for m in messages[1:-1]:
            if current_tokens + len(tokenizer.tokenize(m.text)) > 1000:
                break
            modmessages.insert(1, m)
            current_tokens += len(tokenizer.tokenize(m.text))
        logger.info(f"Final Tokens Decoder Messages: {current_tokens}")
    else:
        modmessages = messages

    Cleanmemorys = ""
    for mem in Context:
        Cleanmemorys += f"Memory|title={mem.title} , content={mem.content} <|> "
    EXAMPLES = []
    for c in DECODER_EXAMPLES:
        example_messages = []
        for m in c.messages:
            if m.user == "Lenard":
                example_messages.append(Message(user=MY_BOT_NAME, text=m.text))
            else:
                example_messages.append(m)
        EXAMPLES.append(Conversation(messages=example_messages))

    decoder=QueryPrompt(
        header=Message(
            "System", f"Instructions for Decoder: {DECODER_INSTRUCTIONS}"
        ),
        examples=DECODER_EXAMPLES,
        convo=Conversation(modmessages + [
            Message("System", f"{Cleanmemorys}")] + [
                               Message("Decoder")]),
    )
    rendered = decoder.render()
    response = await openai.Completion.acreate(
        engine="text-davinci-003",
        prompt=rendered,
        temperature=0,
        top_p=0.9,
        max_tokens=512,
        stop=["||>"],
    )
    text = response["choices"][0]["text"]
    await save_prompt_db("decoder", f"{Cleanmemorys}", text)
    return text, response.usage.total_tokens



async def encoder(messages: List[Message], webresults):
    ### Do a check on what we actually have before we send it OpenAI
    messages = messages [-4:]
    tokens = 0
    memorys = []
    if webresults:
        for web in webresults:
            ### Ok we now have nicely split up Webresults
            ### Time to send the all to OpenAI to get a proper Summary back from the Crappy Webresults to save as Memory and return to our Decision Routine
            CONVO = []
            for c in ENCODER_EXAMPLES:
                encoder_messages = []
                for m in c.messages:
                    if m.user == "Lenard":
                        encoder_messages.append(Message(user=MY_BOT_NAME, text=m.text))
                    else:
                        encoder_messages.append(m)
                CONVO.append(Conversation(messages=encoder_messages))

            encoder = QueryPrompt(
                header=Message(
                    "System", f"Instructions for Encoder: {ENCODER_INSTRUCTIONS}"
                ),
                examples=CONVO,
                convo=Conversation(messages + [Message("System", f"Link = {web.link} , Snippet = {web.snippet} , Content = {web.content}" )] + [Message("Encoder")]),
            )
            rendered = encoder.render()
            response = await openai.Completion.acreate(
                engine="text-davinci-003",
                prompt=rendered,
                temperature=0,
                top_p=0.9,
                max_tokens=512,
                stop=["||>"],
            )
            tokens +=response.usage.total_tokens
            #logger.info(f"DEBUG ENCODER RENDERED PROMPT: {rendered}")
            # Time to take Apart the Answer from OpenAI and put it into a Memory Dataclass ... did i tell you that i hate this stuff ...
            text = response["choices"][0]["text"]
            await save_prompt_db("encoder", f"Link = {web.link} , Snippet = {web.snippet} , Content = {web.content}", text)
            if "<|>" in text:
                title, content = text.split("<|>")
                title = title.split("=")[1].strip()
                content = content.split("=")[1].strip()
                wordcount = len(tokenizer.tokenize(content))

                memory = Memory(title=title.strip("?"), content=content, tokens=wordcount)
                # We can also save every Memory here in Weaviate

                memory_obj = {
                    "title": memory.title,
                    "content": memory.content,
                    "tokens": memory.tokens,
                }
                client.data_object.create(
                    data_object=memory_obj,
                    class_name="Memorys",
                )
                memorys.append(memory)
    return memorys, tokens


async def decision_engine(messages: List[Message]):
    msg_category, msg_searchterms, tokens = await querygenerator(messages)
    wordcount = 0
    Context = []
    if msg_category != "General_Message" or "None":
        if msg_searchterms != ['']:
            # Use asyncio.gather to run websearch and encoding tasks in parallel
            websearch_tasks = [websearch(searchterm) for searchterm in msg_searchterms]
            encoded_tasks = [encoder(messages, web) for web in await asyncio.gather(*websearch_tasks)]
            for webmem, token_usage in await asyncio.gather(*encoded_tasks):
                if webmem:
                    if wordcount < 800:
                        memory = Memory(title=webmem[0].title, content=webmem[0].content, tokens=webmem[0].tokens)
                        Context.append(memory)
                        wordcount += memory.tokens
                        tokens += token_usage
                    else:
                        break
            # Now we load Memorys from the Database:
            db_query_tasks = [listmemory(searchterm) for searchterm in msg_searchterms]
            dbmem_list = await asyncio.gather(*db_query_tasks)
            for dbmem in dbmem_list:
                for mem in dbmem["data"]["Get"]["Memorys"]:
                    if wordcount < 800:
                        memory = Memory(title=mem["title"], content=mem["content"], tokens=mem["tokens"])
                        wordcount += memory.tokens
                        Context.append(memory)
                    else:
                        break
    # We got alot of Memorys now in the Context List and need to send it all to a Decoder to remove Duplicates and create only a Contextlist for our Current Conversation:
    final_context, dec_counter = await decoder(messages, Context)
    tokens += dec_counter
    return final_context, tokens

### Part of the Decision Engine Routine
async def listmemory(question):
    nearText = {
        "concepts": question,
        "distance": 0.7,  # prior to v1.14 use "certainty" instead of "distance"
    }
    result = (
        client.query
        .get('Memorys', ['title', 'content', 'tokens'])
        .with_near_text(nearText)
        .with_limit(1)
        .do()
    )
    return result

### Part of Dynamic Convo Picker
async def listnear(question):
    nearText = {
        "concepts": question,
        "distance": 0.7,  # prior to v1.14 use "certainty" instead of "distance"
    }
    result = (
        client.query
        .get('Examples', ['messageID', 'content'])
        .with_near_text(nearText)
        .with_limit(3)
        .do()
    )

    return result

### Part of Dynamic Convo Picker
def convert_to_json2(message):
    data = {
        'text': message
    }
    return data

def convert_to_json(message):
    data = {
        'text': message.text
    }
    return data

### Part of Dynamic Convo Picker
async def getexamples(messages: List[Message]):
    json_messages = [convert_to_json(m) for m in messages]
    EXAMPLEs = await listnear(json_messages[-1]['text'])
    if EXAMPLEs is None or "Examples" not in EXAMPLEs["data"]["Get"] or not EXAMPLEs["data"]["Get"]["Examples"]:
        CONVOS = EXAMPLE_CONVOS
        CHOOSEN_CONVOS = []
        for c in CONVOS:
            messages = []
            for m in c.messages:
                if m.user == "Lenard":
                    messages.append(Message(user=MY_BOT_NAME, text=m.text))
                else:
                    messages.append(m)
            CHOOSEN_CONVOS.append(Conversation(messages=messages))
        return CHOOSEN_CONVOS
    example_content = EXAMPLEs["data"]["Get"]["Examples"][0]["content"]
    # Create a list of Conversation objects from the example_content list of dictionaries
    example_conversations = []
    example_content = yaml.safe_load(example_content)
    for example in example_content['example_conversations']:
        messages = [dacite.from_dict(Message, message) for message in example['messages']]
        example_conversations.append(dacite.from_dict(Conversation, {'messages': messages}))

    # Create a Config object with the example_conversations list
    config = dacite.from_dict(Config, {"name": MY_BOT_NAME, "instructions": BOT_INSTRUCTIONS,
                                       "example_conversations": example_conversations})
    CONVOS = config.example_conversations
    CHOOSEN_CONVOS = []
    for c in CONVOS:
        messages = []
        for m in c.messages:
            if m.user == "Lenard":
                messages.append(Message(user=MY_BOT_NAME, text=m.text))
            else:
                messages.append(m)
        CHOOSEN_CONVOS.append(Conversation(messages=messages))
    logger.info(f"Choosen the following Example Conversation: {CHOOSEN_CONVOS}")
    return CHOOSEN_CONVOS

async def generate_completion_response(
    messages: List[Message], user: str
) -> CompletionData:
    tokens = 0
    try:
        ## Adding a "Decision Routine" and a "Source Routine" which will modify the Prompt even more with dynamic Data. Totally butchered ofc. ###
        final_context = ""
        final_context, tokens = await decision_engine(messages)
        logger.info(f"we reached DECIOSN IN generate_complete_response{final_context}")
        ### This adds the Example_Convos Dynamic Picker in a butchered Way ###
        CONVOS = await getexamples(messages)
        #logger.info(f"DEBUG EXAMPLE CONVERSATION: {CONVOS}")
        if len(messages) > 2:
            modmessages = [messages[0], messages[-1]]
            messages = messages[::-1]
            current_tokens = sum(len(tokenizer.tokenize(m.text)) for m in modmessages)
            for m in messages[1:-1]:
                if current_tokens + len(tokenizer.tokenize(m.text)) > 2100:
                    print(f"Reached Conversation Limit, Cutting down Conversation Length: {current_tokens}")
                    break
                modmessages.insert(1, m)
                current_tokens += len(tokenizer.tokenize(m.text))
            logger.info(f"Final Tokens Final Response Messages: {current_tokens}")
        else:
            modmessages = messages
        prompt = Prompt(
            header=Message(
                "System", f"Instructions for {MY_BOT_NAME}: {BOT_INSTRUCTIONS}"
            ),
            examples=CONVOS,
            convo=Conversation(modmessages + [Message(MY_BOT_NAME)]),
            date=datetime.datetime.now(),
            context=Message("System", f"Context for current Question:{final_context}")
        )
        rendered = prompt.render()
        ### Here it Ends what we butchered ###
        logger.info(f"DEBUG Rendered Prompt: {rendered}")
        response = await openai.Completion.acreate(
            engine="text-davinci-003",
            prompt=rendered,
            temperature=0.2,
            top_p=0.9,
            max_tokens=512,
            stop=["||>"],
        )
        reply = response.choices[0].text.strip()
        #await save_prompt_db("Final", messages, reply)
        if reply:
            flagged_str, blocked_str = moderate_message(
                message=(rendered + reply)[-500:], user=user
            )
            if len(blocked_str) > 0:
                return CompletionData(
                    status=CompletionResult.MODERATION_BLOCKED,
                    reply_text=reply,
                    status_text=f"from_response:{blocked_str}",
                    tokens=tokens
                )

            if len(flagged_str) > 0:
                return CompletionData(
                    status=CompletionResult.MODERATION_FLAGGED,
                    reply_text=reply,
                    status_text=f"from_response:{flagged_str}",
                    tokens=tokens
                )

        tokens +=response.usage.total_tokens
        return CompletionData(
            status=CompletionResult.OK, reply_text=reply, status_text=None, tokens=tokens
        )
    except openai.error.InvalidRequestError as e:
        if "This model's maximum context length" in e.user_message:
            return CompletionData(
                status=CompletionResult.TOO_LONG, reply_text=None, status_text=str(e), tokens=tokens
            )
        else:
            logger.exception(e)
            return CompletionData(
                status=CompletionResult.INVALID_REQUEST,
                reply_text=None,
                status_text=str(e),
                tokens=tokens
            )
    except Exception as e:
        logger.exception(e)
        return CompletionData(
            status=CompletionResult.OTHER_ERROR, reply_text=None, status_text=str(e), tokens=tokens
        )


async def process_response(
    user: str, thread: discord.Thread, response_data: CompletionData
):
    status = response_data.status
    reply_text = response_data.reply_text
    status_text = response_data.status_text
    token_usage = response_data.tokens
    if status is CompletionResult.OK or status is CompletionResult.MODERATION_FLAGGED:
        sent_message = None
        if not reply_text:
            sent_message = await thread.send(
                embed=discord.Embed(
                    description=f"**Invalid response** - empty response",
                    color=discord.Color.yellow(),
                )
            )
        else:
            ### Here we can add the Log Message on Discord to show Tokenusage:
            # Maybe Move this to utils.py
            # Here we add the token_usage to the sqlite db for the user:
            await update_token_usage(user, token_usage)
            try:
                await send_usage(
                    guild=thread.guild,
                    user=user,
                    tokens=token_usage,
                    url=thread.jump_url
                )
            except Exception as e:
                logger.info(f"No Status-Channelset on Server: {thread.guild}")
                logger.info(f"Token Usage by User: {user}, Tokens-Spent: {token_usage} URL: {thread.jump_url}")
            shorter_response = split_into_shorter_messages(reply_text)
            for r in shorter_response:
                sent_message = await thread.send(r)
        if status is CompletionResult.MODERATION_FLAGGED:
            await send_moderation_flagged_message(
                guild=thread.guild,
                user=user,
                flagged_str=status_text,
                message=reply_text,
                url=sent_message.jump_url if sent_message else "no url",
            )

            await thread.send(
                embed=discord.Embed(
                    description=f"⚠️ **This conversation has been flagged by moderation.**",
                    color=discord.Color.yellow(),
                )
            )
    elif status is CompletionResult.MODERATION_BLOCKED:
        await send_moderation_blocked_message(
            guild=thread.guild,
            user=user,
            blocked_str=status_text,
            message=reply_text,
        )

        await thread.send(
            embed=discord.Embed(
                description=f"❌ **The response has been blocked by moderation.**",
                color=discord.Color.red(),
            )
        )
    elif status is CompletionResult.TOO_LONG:
        await close_thread(thread)
    elif status is CompletionResult.INVALID_REQUEST:
        await thread.send(
            embed=discord.Embed(
                description=f"**Invalid request** - {status_text}",
                color=discord.Color.yellow(),
            )
        )
    else:
        await thread.send(
            embed=discord.Embed(
                description=f"**Error** - {status_text}",
                color=discord.Color.yellow(),
            )
        )