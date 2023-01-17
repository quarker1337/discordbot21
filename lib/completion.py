from enum import Enum
import datetime
import dacite
import yaml
from dataclasses import dataclass
import openai
from lib.moderation import moderate_message
from typing import Optional, List
from lib.constants import (
    BOT_INSTRUCTIONS,
    BOT_NAME,
    WEAVICLIENT,
    EXAMPLE_CONVOS,
)
import discord
from lib.base import Message, Prompt, Conversation, Config
from lib.utils import split_into_shorter_messages, close_thread, logger
from lib.moderation import (
    send_moderation_flagged_message,
    send_moderation_blocked_message,
)
MY_BOT_EXAMPLE_CONVOS = EXAMPLE_CONVOS
MY_BOT_NAME = BOT_NAME


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

async def listnear(question):
    client = WEAVICLIENT
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

def convert_to_json(message):
    data = {
        'text': message.text
    }
    return data

async def getexamples(messages: List[Message]):
    json_messages = [convert_to_json(m) for m in messages]
    EXAMPLEs = await listnear(json_messages[-1]['text'])
    if EXAMPLEs is None or "Examples" not in EXAMPLEs["data"]["Get"] or not EXAMPLEs["data"]["Get"]["Examples"]:
        print("No example conversation found.")
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
    try:
        # Time to butcher this totally
        CONVOS = await getexamples(messages)
        logger.info(f"DEBUG EXAMPLE CONVERSATION: {CONVOS}")
        prompt = Prompt(
            header=Message(
                "System", f"Instructions for {MY_BOT_NAME}: {BOT_INSTRUCTIONS}"
            ),
            examples=CONVOS,
            convo=Conversation(messages + [Message(MY_BOT_NAME)]),
            date=datetime.datetime.now()
        )
        rendered = prompt.render()
        ### Here it Ends what we butchered ###
        logger.info(f"DEBUG Rendered Prompt: {rendered}")

        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=rendered,
            temperature=1.0,
            top_p=0.9,
            max_tokens=512,
            stop=["<|endoftext|>"],
        )

        reply = response.choices[0].text.strip()
        if reply:
            flagged_str, blocked_str = moderate_message(
                message=(rendered + reply)[-500:], user=user
            )
            if len(blocked_str) > 0:
                return CompletionData(
                    status=CompletionResult.MODERATION_BLOCKED,
                    reply_text=reply,
                    status_text=f"from_response:{blocked_str}",
                )

            if len(flagged_str) > 0:
                return CompletionData(
                    status=CompletionResult.MODERATION_FLAGGED,
                    reply_text=reply,
                    status_text=f"from_response:{flagged_str}",
                )

        #reply = "DEBUGGIN"
        return CompletionData(
            status=CompletionResult.OK, reply_text=reply, status_text=None
        )
    except openai.error.InvalidRequestError as e:
        if "This model's maximum context length" in e.user_message:
            return CompletionData(
                status=CompletionResult.TOO_LONG, reply_text=None, status_text=str(e)
            )
        else:
            logger.exception(e)
            return CompletionData(
                status=CompletionResult.INVALID_REQUEST,
                reply_text=None,
                status_text=str(e),
            )
    except Exception as e:
        logger.exception(e)
        return CompletionData(
            status=CompletionResult.OTHER_ERROR, reply_text=None, status_text=str(e)
        )


async def process_response(
    user: str, thread: discord.Thread, response_data: CompletionData
):
    status = response_data.status
    reply_text = response_data.reply_text
    status_text = response_data.status_text
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