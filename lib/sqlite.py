import sqlite3
from typing import List
from lib.utils import(
    logger,
)

async def create_database():
    conn = connect_database()

    conn.execute('''CREATE TABLE USERS
                (ID INT PRIMARY KEY NOT NULL,
                USERNAME    TEXT    NOT NULL,
                TOKENS      INT     NOT NULL,
                LIFETIMETOKENS  INT)
    ;''')

    conn.execute('''CREATE TABLE PROMPTS
                (TYPE       TEXT     NOT NULL,
                PROMPT      TEXT    NOT NULL,
                COMPLETION  TEXT)
        ;''')
    logger.info(f"Created new SQLite Database")
    return

def connect_database():
    conn = sqlite3.connect("bot.db")
    return conn

async def load_db_user(user):
    conn = connect_database()
    cursor = conn.execute("SELECT id, username, tokens, lifetimetokens from USERS WHERE id=?", (user.id,))
    result = cursor.fetchone()
    if result is None:
        conn.execute("INSERT INTO USERS (id, username, tokens, lifetimetokens) VALUES (?,?,?,?)", (user.id, user.name, 250000, 0))
        conn.commit()
        logger.info(f"Created new SQLite Entry for {user.name} with ID: {user.id}")
        return (user.id, user.name, 250000, 0)
    else:
        return result

async def get_db_users():
    conn = connect_database()
    cursor = conn.execute("SELECT id, username, tokens, lifetimetokens from USERS")
    return cursor

async def get_db_prompts():
    conn = connect_database()
    cursor = conn.execute("SELECT type, prompt, completion from PROMPTS")
    return cursor

async def update_token_usage(user, usage):
    conn = connect_database()
    db_user = await load_db_user(user)
    current_tokens = db_user[2]
    lifetime_tokens = db_user[3]
    new_tokens = current_tokens - usage
    new_lifetime_tokens = lifetime_tokens + usage
    if new_tokens < 0:
        new_tokens = 0
    conn.execute("UPDATE USERS SET tokens=?, lifetimetokens=? WHERE id=?", (new_tokens, new_lifetime_tokens, user.id))
    conn.commit()

async def update_balance(user, tokens: int):
    conn = connect_database()
    db_user = await load_db_user(user)
    current_tokens = db_user[2]
    new_tokens = current_tokens + tokens
    conn.execute("UPDATE USERS SET tokens=? WHERE id=?", (new_tokens, user.id))
    conn.commit()
    result = await load_db_user(user)
    return result, current_tokens

### Function that saves all Inputprompts + generated Outputs for later Finetuning of cheaper Models
async def save_prompt_db(type: str, messages, completion: str):
    conn = connect_database()
    print(messages[-1].text)
    print(completion)
    conn.execute("INSERT INTO PROMPTS (type, prompt, completion) VALUES (?,?,?)", (type, messages[-1].text, str(completion)))
    conn.commit()
    logger.info(f"Written New SQLite Prompt Entry: Prompt: {messages[-1]} Completion: {completion}")


