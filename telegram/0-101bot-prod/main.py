import sqlite3
import time
import json
import hashlib
import random
import string
import os
import aiomysql
from telegram import InlineQueryResultPhoto, InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Application, InlineQueryHandler, ChosenInlineResultHandler, CallbackContext


db_pool = None

no_item_all = {
    'pet101bot': 'Всех манулов уже погладили',
    'honk101bot': 'Всех гусей уже запустили',
    'beo101bot': 'Все граффити уже нарисовали'
}


async def inline_query(update: Update, ctx: CallbackContext):
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            user = update.inline_query.from_user
            raw = json.dumps(update.to_dict(), ensure_ascii=False)
            now = time.time()
            no_item = no_item_all[os.getenv("BOT_NAME")]

            await cur.execute("SELECT bot, number, url, thumb, comment FROM NFTs WHERE owner_id = %s ORDER BY CASE WHEN bot = %s THEN 1 ELSE 2 END;",
                                (user['id'], os.getenv("BOT_NAME"),))
            nfts = await cur.fetchall()
            nfts = [nft + (''.join(random.choices(string.ascii_letters +
                            string.digits, k=16)),) for nft in nfts]

            if len(nfts) == 0:
                id = ''.join(random.choices(
                    string.ascii_letters + string.digits, k=16))
                await cur.execute("INSERT INTO Queries (timestamp, query_id, number, user_id, username, bot, raw) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                            (now, id, -1, user['id'], user['username'], os.getenv("BOT_NAME"), raw))

                await update.inline_query.answer([InlineQueryResultArticle(id=id, title=no_item,
                                                                            input_message_content=InputTextMessageContent(no_item))], cache_time=0)
            else:
                await cur.executemany(
                    "INSERT INTO Queries (timestamp, query_id, number, user_id, username, bot, raw) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    [(now, id, number, user['id'], user['username'], bot, raw) for (bot, number, url, thumb, comment, id) in nfts])

                await update.inline_query.answer([InlineQueryResultPhoto(id=id, photo_url=url, thumbnail_url=thumb, caption=comment) for
                                                    (bot, number, url, thumb, comment, id) in nfts], cache_time=0)



async def inline_result(update, ctx):
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("INSERT INTO Results (timestamp, result_id, raw, bot) VALUES (%s,%s,%s,%s)",
                        (time.time(), update.chosen_inline_result.result_id, json.dumps(update.to_dict(), ensure_ascii=False), os.getenv("BOT_NAME")))


async def init(app: Application) -> None:
    global db_pool
    db_pool = await aiomysql.create_pool(
        host="tgrmariadb",
        port=3306,
        user="101bot",
        password=os.getenv("DB_PASSWORD"),
        db="101bot",
        minsize=1, maxsize=3, autocommit=True
    )

    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT bot, number, owner_id FROM NFTs ORDER BY bot, number;")
            data = await cur.fetchall()

            hash_o = hashlib.sha256()
            hash_o.update(json.dumps(data).encode())
            hash = hash_o.hexdigest()

            if hash != 'afeb306b9ede3bdfaf4bcadebf7a5e34ae150423b3b93d8535337966d73ae647':
                raise Exception("bad NFT owners")


# https://core.telegram.org/bots/api#available-methods
application: Application = Application.builder().token(os.getenv("A101BOT_API_KEY")).post_init(init).build()
application.add_handler(ChosenInlineResultHandler(inline_result))
application.add_handler(InlineQueryHandler(inline_query))
application.run_polling()
