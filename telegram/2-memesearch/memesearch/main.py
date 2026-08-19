from telegram.ext import Application, MessageHandler, filters
from telegram import InputMediaPhoto
from openai import AsyncOpenAI
import numpy as np
import time
import os

async def search(update, context):
    global memes

    started = time.time()

    response = await client.embeddings.create(input=[update.message.text], model="text-embedding-3-large")
    embedding = response.data[0].embedding

    embedded = time.time()

    cosines = memes['embedding'] @ np.array(embedding)

    top10_indices = np.argpartition(-cosines, 10)[:10]
    top10_sorted = top10_indices[np.argsort(-cosines[top10_indices])]
    top10_hashes = memes['hash'][top10_sorted]

    calculated = time.time()

    await update.message.reply_media_group(
        media=[InputMediaPhoto(open(f"/usr/src/app/memes/{hash.hex()}.jpg", 'rb')) for hash in top10_hashes])

    sent = time.time()

    await update.message.reply_text(text=f"#trace embedding {embedded - started:.3f}s, calculate {calculated - embedded:.3f}s, sent {sent - calculated:.3f}s")


async def init(app: Application) -> None:
    global memes
    started = time.time()

    meme_dtype = np.dtype([('hash', 'S32'), ('embedding', 'f8', 3072)])
    memes = np.memmap("/usr/src/app/db/memes.bin", dtype=meme_dtype, mode='r')

    await app.bot.send_message(chat_id=int(os.getenv("ADMIN_UID")), text=f"#trace init {time.time() - started:.3f}s")

client = AsyncOpenAI(api_key=os.getenv("OPENAI_KEY"))

# https://core.telegram.org/bots/api#available-methods
application: Application = Application.builder().token(os.getenv("API_KEY")).post_init(init).build()
application.add_handler(MessageHandler(filters.TEXT & filters.User(user_id=int(os.getenv("ADMIN_UID"))), search))
application.run_polling()
