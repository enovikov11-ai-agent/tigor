import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Environment variable TELEGRAM_BOT_TOKEN is missing")


async def purge_inline_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message # here is bug, need @pic or sth
    if not msg or not msg.via_bot or msg.via_bot in ("pic", "gif", "pet101bot", "honk101bot", "beo101bot"):
        return

    try:
        await msg.delete()
    except Exception as e:
        print(e)


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.ALL, purge_inline_message))
app.run_polling(allowed_updates=["message"])
