# OpenAI powered Discord Bot  
This is a Discord bot built using Python and the Discord API. The bot is built using the `discord.py` library and utilizes "cogs" to separate different functions into different files.

This bot incorporates a reworked version of the OpenAI's gpt-discord-bot, using OpenAI's completion and moderation API for text-davinci-003 model based conversations and message filtering. The chat command starts a public thread for users to interact with the bot. Inspired by Blenderbot2 Architecture, the processing pipeline is as follows:

1. User sends message
2. OpenAI moderation endpoint checks message
3. GPT3 query generator classifies message into 3 categories: general message, task, or question
4. GPT3 encoder analyzes 2 web results for task or question and saves memory in Weaviate DB
5. GPT3 decoder generates summary of web content and memory
6. GPT3 final generates answer to user message
7. OpenAI moderation endpoint checks message before sending
8. Chatbot answers

__Note__: This reworked version is expensive to run, with 5 completion requests and 2 search requests to Google's Custom Search API per user interaction.

## Getting Started
Requirements:
* OpenAI API Key
* Discord Bot API Key
* Google Custom JSON Search API Key and Custom Search ID
* Weaviate DB Setup and accessible by your Chatbot

Steps:
1. Install dependencies with `pip install -r requirements.txt`
2. Create a `config.ini` file with Discord API, OpenAI API and Google Search key details, using `example.ini` as reference.
3. Set up Weaviate database by following instructions on https://weaviate.io/developers/weaviate/current/installation/docker-compose.html.
4. Run the bot by executing the main.py file with Python.
5. Run the `!db createschema` Command once in a set Command Channel to setup the Weaviate Schema for the Bot.
6. Run the `!db sqlite createusersdb` Command once to setup the SQLite DB for Bot.
7. You should be able to use the /info and /chat command now.

### Weaviate Setup
In order to use the advanced features of this bot, you will need to install a Weaviate database. You can do this by following the instructions on this page: https://weaviate.io/developers/weaviate/current/installation/docker-compose.html

You can use the following example Docker Compose file as a reference:

```yaml
version: '3.4'
services:
  weaviate:
    command:
    - --host
    - 0.0.0.0
    - --port
    - '8080'
    - --scheme
    - http
    image: semitechnologies/weaviate:1.17.0
    ports:
    - 8080:8080
    restart: on-failure:0
    environment:
      OPENAI_APIKEY: $OPENAI_APIKEY
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'text2vec-openai'
      ENABLE_MODULES: 'text2vec-openai'
      CLUSTER_HOSTNAME: 'node1'
```
Make sure to set the correct version of Weaviate image you want to use and also set the correct OpenAI API key in the environment section.

__Note__: The example Weaviate Docker Compose has no authentication and Persistent Storage, check the official Documentation howto add this.

__Warning__: Deleting the Weaviate Database will delete all previously generated Memorys!

## Running the Bot  
To run the bot, simply execute the `main.py` file using Python. The bot will automatically load all cogs (files ending in `.py`) in the `cogs` directory and start running.

## Hardware Requirements
As the Bot uses GPT2 Tokenizer and Weaviate the Bot requires quite some CPU Computing Power.

## Customizing the Bot  
You can add additional functionality to the bot by creating new cogs and placing them in the `cogs` directory. The provided `ping.py` and `test.py` cogs serve as examples of how to create and use cogs.  
  
## Usage  
The bot has a command prefix of `!` and currently has two commands: `!ping` and `!test`. The `!ping` command will simply respond with "Pong", while the `!test` command will repeat the message that was sent. You can also use the `!help` command to display a list of commands that the bot has.  

## Attribution

This repository includes code from the following third-party libraries:

- [OpenAI GPT-Discord-Bot](https://github.com/openai/gpt-discord-bot/)
  - `src/main.py`: Used in `cogs/quarks.py`
  - `src/*.py`: Used in `lib/*.py`
  - `src/config.yaml`: Used in `lib/config.yaml`

This code is used under the terms of the MIT License, a copy of which can be found in the `LICENSE` file.

### References  
* [https://github.com/openai/gpt-discord-bot/]
* [https://discordpy.readthedocs.io/en/stable/ext/commands/extensions.html]
* [https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html]
* [https://openai.com/]
* [https://beta.openai.com/docs/introduction]
* [https://parl.ai/projects/blenderbot2/]
