# -*- coding: utf-8 -*-

from telegram.ext import Updater
from telegram.ext import CommandHandler, MessageHandler, Filters
import sqlite3
import json
import random
import re

from constants import ALLOWED_USERS, TOKEN, ADMIN_NAME

updater = Updater(token=TOKEN, use_context=True)

import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

help_text = """
Привет, {}!

Я бот помощник тайного санты:)
Не стоит терять время и пора приступать к самому интересному - выбору и раздаче подарков!
Вот команды, которые могут помочь тебе в этом непростом и увлекательном деле:


* /set_wishes
Команда для выбора пожеланий. Можно указать сразу несколько подарков, чтобы у твоего анонимного Санты был выбор, или же несколько небольших приятных мелочей) Помни, что общий бюджет подарка 2000-2500 рублей.

Пример: /set_wishes
Затем можно посылать свой список пожеланий одним сообщением.
Вызывая команду повторно, можно поменять список желаний.


* /get_wishes
Так ты можешь посмотреть установленные ранее пожелания и убедиться, что я все правильно понял:)
Пример: /get_wishes


Как только все соберутся и передадут мне свои пожелания, я скажу, что делать дальше)
"""


def sql_connect():
    conn = sqlite3.connect("wishes.sqlite")
    return conn


def sql_wishes_update(chat_id, wishes, name):

    conn = sql_connect()
    cursor = conn.cursor()

    old_wishes = sql_get_wishes(chat_id)
    if old_wishes == None:
        query = """INSERT INTO wishes
            (chat_id, wishes, name)
            VALUES
            (?, ?, ?)"""
        cursor.execute(query, (chat_id, wishes, name))
    else:
        query = """UPDATE wishes
            SET wishes=? WHERE chat_id=?"""

        cursor.execute(query, (wishes, chat_id))
    conn.commit()
    conn.close()


def sql_get_wishes(chat_id):
    conn = sql_connect()
    cursor = conn.cursor()
    query = """SELECT wishes FROM wishes WHERE chat_id='{0}';"""
    query = query.format(chat_id)
    cursor.execute(query)
    wishes = cursor.fetchone()

    conn.close()
    return wishes


def sql_create_table():

    conn = sql_connect()
    cursor = conn.cursor()
    query = """CREATE TABLE IF NOT EXISTS wishes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_id TEXT NOT NULL UNIQUE,
  wishes TEXT NOT NULL,
  name TEXT NOT NULL
)"""

    cursor.execute(query)

    conn.commit()
    conn.close()


def sql_get_all_lines():
    conn = sql_connect()
    cursor = conn.cursor()
    query = """SELECT * FROM wishes"""
    cursor.execute(query)
    wishes = cursor.fetchall()

    conn.close()
    return wishes


def start(update, context):
    if not auth_check(update):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Nothing here")
        return
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=help_text.format(update.effective_user.first_name),
    )


def set_wishes(update, context):
    if not auth_check(update):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Nothing here")
        return

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Скорее присылай мне свои пожелания) Начни со слов: Список пожеланий",
    )


def get_wishes(update, context):
    if not auth_check(update):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Nothing here")
        return
    wishes = sql_get_wishes(update.effective_chat.id)
    if wishes != None:
        wishes_list = json.loads(wishes[0])
        wishes = "Список твоих самых заветных пожеланий:\n"
        wishes += wishes_list + "\n"
    else:
        wishes = "Твой список подарков пуст, поторопись)"

    context.bot.send_message(chat_id=update.effective_chat.id, text=wishes)


def get_deny(name):
    for i in ALLOWED_USERS:
        if name == i["name"]:
            return i["deny"]


def get_user_by_name_from_db_res(name, results):
    for i in results:
        if name == i[3]:
            return i

    return None


def generate_pairs():
    if len(ALLOWED_USERS) < 2:
        return []
    users_to = ALLOWED_USERS[:]
    errFlag = True
    while errFlag:
        errFlag = False
        random.shuffle(users_to)
        for i, user in enumerate(ALLOWED_USERS):
            if (
                get_deny(user["name"]) == users_to[i]["name"]
                or user["name"] == users_to[i]["name"]
            ):
                errFlag = True
                break

    return list(zip(ALLOWED_USERS, users_to))


def generate_santa_messages():
    messages = []
    users_db = sql_get_all_lines()
    pairs = generate_pairs()
    for pair in pairs:
        messages.append(
            [
                get_user_by_name_from_db_res(pair[0]["name"], users_db),
                get_user_by_name_from_db_res(pair[1]["name"], users_db),
            ]
        )

    return messages


def run_game(update, context):
    if not admin_check(update):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Nothing here")
        return
    pairs = generate_santa_messages()
    for pair in pairs:
        text = "А теперь самое интересное! Можно приступать к поиску подарков! Ты - тайный санта для... *барабанная дробь* .. {0}\n".format(
            pair[1][3].split(":::")[0]
        )
        text += "Список пожеланий:\n"
        text += json.loads(pair[1][2])
        text += "\nДааа... нелегка твоя участь;) но я верю, что ты справишься)"
        context.bot.send_message(chat_id=pair[0][1], text=text)


def unknown(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Не знаю таких команд :( Я всего лишь помощник Санты",
    )


def set_wishes_text(update, context):
    if update.effective_message.text.lower().startswith("список пожеланий"):
        p = re.compile("^Список пожеланий\S*", re.I)
        text = p.sub("", update.effective_message.text)
        wishes = json.dumps(text)
        sql_wishes_update(
            update.effective_chat.id,
            wishes,
            update.effective_user.first_name + ":::" + update.effective_user.last_name,
        )

        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Я всё записал, можешь быть уверен)"
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=help_text.format(update.effective_user.first_name),
        )


def auth_check(update):
    name = update.effective_user.first_name + ":::" + update.effective_user.last_name
    flag = False
    for i in ALLOWED_USERS:
        if i["name"] == name:
            flag = True
            break
    return flag


def admin_check(update):
    name = update.effective_user.first_name + ":::" + update.effective_user.last_name
    return name == ADMIN_NAME


dispatcher = updater.dispatcher

start_handler = CommandHandler("start", start)
message_handler = MessageHandler(Filters.text, set_wishes_text)
help_handler = CommandHandler("help", start)
set_wishes_handler = CommandHandler("set_wishes", set_wishes)
get_wishes_handler = CommandHandler("get_wishes", get_wishes)
run_game_handler = CommandHandler("run_game", run_game)
unknown_handler = MessageHandler(Filters.command, unknown)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(message_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(set_wishes_handler)
dispatcher.add_handler(get_wishes_handler)
dispatcher.add_handler(run_game_handler)
dispatcher.add_handler(unknown_handler)

sql_create_table()
updater.start_polling()
