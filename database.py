# database.py
import sqlite3
import logging
from typing import List, Tuple, Optional
import pandas as pd

logger = logging.getLogger(__name__)
DATABASE_NAME = "DT_bot.db"


def create_tables():
    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT UNIQUE,
                answer TEXT
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                phone TEXT UNIQUE,
                email TEXT UNIQUE
            );

            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY,
                question TEXT,
                response TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        logger.info("Tables created")


def execute_query(query: str, params: tuple = ()) -> Optional[List[Tuple]]:
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                return cur.fetchall()
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")


def update_faq(file_path: str, mode: str = "merge") -> Tuple[int, int]:
    df = pd.read_excel(file_path)
    new, updated = 0, 0

    for _, row in df.iterrows():
        exists = execute_query("SELECT 1 FROM faq WHERE question = ?", (row['question'],))

        if exists and mode == "merge":
            execute_query("UPDATE faq SET answer = ? WHERE question = ?",
                          (row['answer'], row['question']))
            updated += 1
        else:
            execute_query("INSERT INTO faq (question, answer) VALUES (?, ?)",
                          (row['question'], row['answer']))
            new += 1 if not exists else 0

    return new, updated