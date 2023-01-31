import sqlite3
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
    logger.info(f"Created new SQLite Database")
    return

def connect_database():
    conn = sqlite3.connect("bot.db")
    return conn

def update_user(user):
    print(user.id)
    print("TODO")

def check_balance(user):
    balance = 50000
    return balance

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

def get_db_users():
    conn = connect_database()
    cursor = conn.execute("SELECT id, username, tokens, lifetimetokens from USERS")
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

### TODO Build a Function that saves all generated Prompts for later Finetuning of cheaper Models