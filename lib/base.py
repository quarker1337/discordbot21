from dataclasses import dataclass
from typing import Optional, List
import datetime

SEPARATOR_TOKEN = "<|endoftext|>"


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
class Conversation:
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
    example_conversations: List[Conversation]


@dataclass
class Prompt:
    header: Message
    examples: List[Conversation]
    convo: Conversation
    date: Optional[datetime.datetime] = None
    def __init__(self, header: Message, examples: List[Conversation], convo: Conversation, date: Optional[datetime.datetime] = None):
        self.header = header
        self.examples = examples
        self.convo = convo
        self.date = date if date else datetime.datetime.now()
    def render(self):
        date_string = self.date.strftime("%Y-%m-%d %H:%M:%S")
        output = []
        output.append(f"System Date: {date_string}\n")
        output.append(self.header.render()+"\n")
        output.append(Message("System", "Example conversations:").render()+"\n")
        for conversation in self.examples:
            output.append(conversation.render()+"\n")
        output.append(Message("System", "Current conversation:").render()+"\n")
        output.append(self.convo.render())
        return SEPARATOR_TOKEN.join(output)