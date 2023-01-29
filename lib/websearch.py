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
    """
    This function performs a web search for a given search term and returns a list of `Websearch` objects.

    Parameters:
        searchterm (str): The term to search for.

    Returns:
        List[Websearch]: A list of `Websearch` objects with the search results.
    """
    logger.info(f"DEBUG: websearch starting with searchterm: {searchterm}")

    # Check if the search term is valid
    if not searchterm or len(searchterm) == 0:
        raise ValueError("Invalid search term. Please enter a valid search term.")
        return

    api_key = GAPIKEY
    search_engine_id = GAPIID
    query = searchterm
    num_results = 1

    url = f'https://www.googleapis.com/customsearch/v1?key={api_key}&cx={search_engine_id}&q={query}&num={num_results}'
    response = requests.get(url)

    # Check if the response is not successful
    if response.status_code != 200:
        #raise Exception("Request failed with status code " + str(response.status_code))
        logger.error("Request failed with status code %s", response.status_code)
        return

    # Check if the response contains the 'items' key
    if 'items' not in response.json():
        #raise Exception("Response does not contain the 'items' key")
        logger.error("Response does not contain the 'items' key")
        return

    results = response.json()['items']
    websearches = []
    for result in results:
        link = result["link"]
        snippet = result["snippet"]
        try:
            response = requests.get(link, timeout=3)
        except requests.exceptions.Timeout as e:
                logger.error("Timeout occurred: %s", e)
                return

        if response.status_code != 200:
            logger.error("Request failed with status code %s", response.status_code)

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            p_tags = soup.find_all("p")
            if not p_tags:
                text = soup.get_text()
            else:
                text = ""
                for p_tag in p_tags:
                    text += p_tag.get_text()
        except Exception as e:
            logger.error("Failed to parse page %s: %s", link, e)
            return

        mystring_words = text.split()
        n = 1200
        for i in range(1):
            string = ' '.join(mystring_words[i:i + n])
            websearch = Websearch(link=link, snippet=snippet)
            websearch.content = string
            logger.debug("Websearch content: %s", websearch.content)
            websearch.tokens = len(tokenizer.tokenize(websearch.content))
            websearches.append(websearch)

    return websearches
