import discord
import requests
from bs4 import BeautifulSoup
from transformers import GPT2Tokenizer
from discord.ext import commands
from lib.base import Websearch
from lib.utils import (
    logger,
    split_into_shorter_messages,
)
from lib.constants import (
    WEAVICLIENT,
    GAPIKEY,
    GAPIID
)

tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

async def websearch(searchterm: str):
    logger.info(f"DEBUG: websearch starting  with searchterm: {searchterm}")
    api_key = GAPIKEY
    search_engine_id = GAPIID
    query = searchterm
    num_results = 1

    url = f'https://www.googleapis.com/customsearch/v1?key={api_key}&cx={search_engine_id}&q={query}&num={num_results}'
    response = requests.get(url)
    print(response)
    if 'items' not in response.json():
        return None
    results = response.json()['items']
    websearches = []
    for result in results:
        print(result)
        link = result["link"]
        snippet = result["snippet"]
        response = requests.get(link)
        soup = BeautifulSoup(response.text, "html.parser")
        p_tags = soup.find_all("p")
        if not p_tags:
            text = soup.get_text()
        else:
            text = ""
            for p_tag in p_tags:
                text += p_tag.get_text()
        length = len(tokenizer.tokenize(text))
        mystring_words = text.split()
        n = 1200  # number of words in each string ... its roughly 2000 real tokens
        #for i in range(0, len(mystring_words), n): # This is really expensive, only use this for demonstrations, to get more infos just increase the range(1) to range(3)
        for i in range(1):
            string = ' '.join(mystring_words[i:i + n])
            websearch = Websearch(link=link, snippet=snippet)
            websearch.content = string
            print(websearch.content)
            websearch.tokens = len(tokenizer.tokenize(websearch.content))
            websearches.append(websearch)

    return websearches
