from dataclasses import dataclass
from typing import Optional, List
import datetime

SEPARATOR_TOKEN = "||>"

@dataclass(frozen=True)
class Message:
    user: str
    text: Optional[str] = None

    def render(self):
        result = self.user + ":"
        if self.text is not None:
            result += " " + self.text
        return result

@dataclass
class Websearch:
    link: str
    snippet: str
    content: Optional[str] = None
    tokens: Optional[int] = 0

@dataclass
class Memory:
    title: str
    content: str

@dataclass
class Conversation:
    messages: List[Message]

    def prepend(self, message: Message):
        self.messages.insert(0, message)
        return self

    def render(self):
        return f"\n{SEPARATOR_TOKEN}".join(
            [message.render() for message in self.messages]
        )

@dataclass
class Examples:
    messages: List[Message]

    def prepend(self, message: Message):
        self.messages.insert(0, message)
        return self

    def render(self):
        return f"\n{SEPARATOR_TOKEN}".join(
            [message.render() for message in self.messages]
        )

@dataclass(frozen=True)
class Config:
    name: str
    instructions: str
    query_instructions: str
    encoder_instructions: str
    decoder_instructions: str
    example_conversations: List[Conversation]
    query_examples: List[Examples]
    encoder_examples: List[Examples]
    decoder_examples: List[Examples]


@dataclass
class Prompt:
    header: Message
    examples: List[Conversation]
    convo: Conversation
    context: Message
    date: Optional[datetime.datetime] = None
    def __init__(self, header: Message, examples: List[Conversation], convo: Conversation, context: Message, date: Optional[datetime.datetime] = None):
        self.header = header
        self.examples = examples
        self.convo = convo
        self.date = date if date else datetime.datetime.now()
        self.context = context
    def render(self):
        date_string = self.date.strftime("%Y-%m-%d %H:%M:%S")
        output = []
        output.append(f"System Date: {date_string}\n")
        output.append(self.header.render()+"\n")
        output.append(self.context.render()+"\n")
        output.append(Message("System", "Example conversations:").render()+"\n")
        for conversation in self.examples:
            output.append(conversation.render()+"\n")
        output.append(Message("System", "Current conversation:").render()+"\n")
        output.append(self.convo.render())
        return SEPARATOR_TOKEN.join(output)

@dataclass
class QueryPrompt:
    header: Message
    examples: List[Conversation]
    convo: Conversation
    def __init__(self, header: Message, examples: List[Conversation], convo: Conversation
                 ):
        self.header = header
        self.examples = examples
        self.convo = convo
    def render(self):
        output = []
        output.append(self.header.render() + "\n")
        output.append(Message("System", "Example conversations:").render() + "\n")
        for conversation in self.examples:
            output.append(conversation.render() + "\n")
        output.append(Message("System", "Current conversation:").render() + "\n")
        output.append(self.convo.render())
        return SEPARATOR_TOKEN.join(output)

