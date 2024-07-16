import sqlite3
from sqlite3 import Error
import json
import os
from datetime import datetime
import asyncio
import aiosqlite


async def check_db():
    async with aiosqlite.connect('card_cnt.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute('''CREATE TABLE IF NOT EXISTS tables2
                            (table_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            table_name TEXT,
                            reg_time TEXT,
                            min_cost INTEGER,
                            max_cost INTEGER,
                            user_id INTEGER,
                            verified_status BOOL,
                            FOREIGN KEY (user_id) REFERENCES users(tg_id))''')
        await cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                            (tg_id INTEGER PRIMARY KEY, 
                            user_name TEXT)''')


async def get_table(user_id):
    await check_db()
    async with aiosqlite.connect('card_cnt.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM tables2 WHERE user_id = ?", (user_id,))
        product = await cursor.fetchone()
        if product:
            return product
        else:
            return False


async def add_table(table_name, min_cost, max_cost, user_id):
    await check_db()
    async with aiosqlite.connect('card_cnt.db') as conn:
        cursor = await conn.cursor()
        reg_time = datetime.now().strftime('%d-%m-%Y')
        await cursor.execute("INSERT INTO tables2 (table_name, reg_time, min_cost, max_cost, user_id) "
                             "VALUES (?, ?, ?, ?, ?)", (table_name, reg_time, min_cost, max_cost, user_id))
        await conn.commit()
        await conn.close()


async def check_table(table_name):
    await check_db()
    async with aiosqlite.connect('card_cnt.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM tables2 WHERE table_name = ?", (table_name,))
        table = await cursor.fetchone()
        if table:
            return table
        else:
            return False


async def add_user(tg_id, user_name):
    await check_db()
    async with aiosqlite.connect('card_cnt.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("INSERT INTO users (tg_id, user_name) VALUES (?, ?)", (tg_id, user_name))
        await conn.commit()


async def get_user(tg_id=None):
    await check_db()
    async with aiosqlite.connect('card_cnt.db') as conn:
        if tg_id:
            result = await conn.execute_fetchall("SELECT * FROM users WHERE user_id = ?", (tg_id,))
        else:
            result = await conn.execute_fetchall("SELECT * FROM users")
        return result


async def get_unverified_table():
    await check_db()
    async with aiosqlite.connect('card_cnt.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM tables2 WHERE verified_status = 0")
        product = await cursor.fetchall()
        if product:
            return product
        else:
            return False


async def update_verified_status():
    await check_db()
    async with aiosqlite.connect('card_cnt.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("""UPDATE tables2 SET verified_status = 1""")
        await conn.commit()


if __name__ == "__main__":
    asyncio.run(update_verified_status())
    print(asyncio.run(get_unverified_table()))
    print(asyncio.run(get_user()))

