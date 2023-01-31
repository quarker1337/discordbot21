from dotenv import load_dotenv
import configparser
import os
import dacite
import weaviate
import yaml
from typing import Dict, List
from lib.base import Config

load_dotenv()


# move Example Conversations towards completion.py as we dynamically load Example Conversations on each prompt build now!

# load config.yaml
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(SCRIPT_DIR, "config.yaml"), "r") as file:
    CONFIG = dacite.from_dict(Config, yaml.safe_load(file))
# load config.ini File
configfile = os.path.dirname(os.path.dirname(__file__)) + "/config.ini"
config = configparser.ConfigParser()
config.read(configfile)

# DB Client
WEAVICLIENT = weaviate.Client(config['WEAVIATE']['URL'])

# ADMINSTUFF
ADMINUSER = int(config['GENERAL']['ADMIN_ID'])
EXAMPLESCHANNEL = config['GENERAL']['EXAMPLESCHANNEL'].split(',')
EXAMPLESCHANNEL = [int(x.strip()) for x in EXAMPLESCHANNEL]


# gpt-discord-bot Default Settings
BOT_NAME = CONFIG.name
BOT_INSTRUCTIONS = CONFIG.instructions
EXAMPLE_CONVOS = CONFIG.example_conversations

# quark-decision engine Settings
QUERY_INSTRUCTIONS = CONFIG.query_instructions
QUERY_EXAMPLES = CONFIG.query_examples

ENCODER_INSTRUCTIONS = CONFIG.encoder_instructions
ENCODER_EXAMPLES = CONFIG.encoder_examples

DECODER_INSTRUCTIONS = CONFIG.decoder_instructions
DECODER_EXAMPLES = CONFIG.decoder_examples

# Google API Keys
GAPIKEY = config['GOOGLE']['GOOGLEAPIKEY']
GAPIID = config['GOOGLE']['GOOGLE_CUSTOMSEARCH_ID']

# Discord Stuff
DISCORD_BOT_TOKEN = config['DISCORD']['TOKEN']
DISCORD_CLIENT_ID = config['DISCORD']['CLIENT_ID']
OPENAI_API_KEY = config['OpenAI']['TOKEN']

ALLOWED_SERVER_IDS: List[int] = []
server_ids = config['OpenAI']['ALLOWED_SERVERIDS'].split(",")
for s in server_ids:
    ALLOWED_SERVER_IDS.append(int(s))

SERVER_TO_MODERATION_CHANNEL: Dict[int, int] = {}
server_channels = config['OpenAI']['MOD_CHANNELS'].split(",")
for s in server_channels:
    values = s.split(":")
    SERVER_TO_MODERATION_CHANNEL[int(values[0])] = int(values[1])

SERVER_TO_SYSTEMCHANNEL: Dict[int, int] = {}
sysserver_channels = config['GENERAL']['SYSTEMCHANNEL'].split(",")
for s in sysserver_channels:
    values = s.split(":")
    SERVER_TO_SYSTEMCHANNEL[int(values[0])] = int(values[1])

SERVER_TO_COMMANDCHANNEL: Dict[int, int] = {}
command_channels = config['OpenAI']['ACTIVE_COMMAND_CHANNELS'].split(",")
for s in command_channels:
    values = s.split(":")
    SERVER_TO_COMMANDCHANNEL[int(values[0])] = int(values[1])

# Send Messages, Create Public Threads, Send Messages in Threads, Manage Messages, Manage Threads, Read Message History, Use Slash Command
BOT_INVITE_URL = f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&permissions=328565073920&scope=bot"

MODERATION_VALUES_FOR_BLOCKED = {
    "hate": 0.5,
    "hate/threatening": 0.1,
    "self-harm": 0.2,
    "sexual": 0.5,
    "sexual/minors": 0.2,
    "violence": 0.7,
    "violence/graphic": 0.8,
}

MODERATION_VALUES_FOR_FLAGGED = {
    "hate": 0.4,
    "hate/threatening": 0.05,
    "self-harm": 0.1,
    "sexual": 0.3,
    "sexual/minors": 0.1,
    "violence": 0.1,
    "violence/graphic": 0.1,
}

SECONDS_DELAY_RECEIVING_MSG = (
    3  # give a delay for the bot to respond so it can catch multiple messages
)
MAX_THREAD_MESSAGES = 200
ACTIVATE_THREAD_PREFX = "💬✅"
INACTIVATE_THREAD_PREFIX = "💬❌"
MAX_CHARS_PER_REPLY_MSG = (
    1900  # discord has a 2k limit, we just break message into 1.5k
)