# Basic Discord Bot  
This is a simple Discord bot built using Python and the Discord API. The bot is built using the `discord.py` library and utilizes "cogs" to separate different functions into different files.

## Additional Features
This bot also incorporates the use of gpt-discord-bot from OpenAI which uses OpenAI's completions and moderations API to have conversations with the `text-davinci-003` model and filter messages. The bot includes a `/chat` command that starts a public thread where users can interact with the model, and the thread will be closed when the context limit is reached or a maximum message count is reached.

## Getting Started  
To get started, you will need to have Python 3 and the `discord.py` library installed. You can install the necessary dependencies by running `pip install -r requirements.txt`. 

You will also need to create a `config.ini` file with your Discord API token and fill in the necessary OpenAI API key and Discord client ID details. An `example.ini` file is provided as a reference.
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
 

## Running the Bot  
To run the bot, simply execute the `main.py` file using Python. The bot will automatically load all cogs (files ending in `.py`) in the `cogs` directory and start running.  
  
## Customizing the Bot  
You can add additional functionality to the bot by creating new cogs and placing them in the `cogs` directory. The provided `ping.py` and `test.py` cogs serve as examples of how to create and use cogs.  
  
## Usage  
The bot has a command prefix of `!` and currently has two commands: `!ping` and `!test`. The `!ping` command will simply respond with "Pong", while the `!test` command will repeat the message that was sent. You can also use the `!help` command to display a list of commands that the bot has.  

## Attribution

This repository includes code from the following third-party libraries:

- [OpenAI GPT-Discord-Bot](https://github.com/openai/gpt-discord-bot/blob/main/README.md)
  - `src/main.py`: Used in `cogs/quarks.py`
  - `src/*.py`: Used in `lib/*.py`
  - `src/config.yaml`: Used in `lib/config.yaml`

This code is used under the terms of the MIT License, a copy of which can be found in the `LICENSE` file.

### References  
* [https://github.com/openai/gpt-discord-bot/blob/main/README.md]
* [https://discordpy.readthedocs.io/en/stable/ext/commands/extensions.html]  
* [https://openai.com/]
* [https://beta.openai.com/docs/introduction]
* [https://github.com/openai/gpt-discord-bot/blob/main/README.md]