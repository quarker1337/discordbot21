
# Basic Discord Bot  
This is a simple Discord bot built using Python and the Discord API. The bot is built using the **discord.py** library and utilizes "cogs" to separate different functions into different files.  
  
## Getting Started  
To get started, you will need to have Python 3 and the **discord.py** library installed. You can install the necessary dependencies by running **pip install -r requirements.txt**.  
  
You will also need to create a **config.ini** file with your Discord API token. An **example.ini** file is provided as a reference.  
  
## Running the Bot  
To run the bot, simply execute the **main.py** file using Python. The bot will automatically load all cogs (files ending in **.py**) in the **cogs** directory and start running.  
  
## Customizing the Bot  
You can add additional functionality to the bot by creating new cogs and placing them in the **cogs** directory. The provided **ping.py** and **test.py** cogs serve as examples of how to create and use cogs.  
  
## Usage  
he bot has a command prefix of **!** and currently has two commands: **!ping** and **!test**. The **!ping** command will simply respond with "Pong", while the **!test** command will repeat the message that was sent.  
  
### Links  
* [https://discordpy.readthedocs.io/en/stable/ext/commands/extensions.html]  
* [https://openai.com/]
