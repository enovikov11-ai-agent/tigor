import sqlite3
import os
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, InlineQueryHandler, CommandHandler


DATABASE_URL = 'database.sqlite'

def connect_to_database():
    connection = sqlite3.connect(DATABASE_URL)
    return connection

def get_image_urls():
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("SELECT url FROM images WHERE used=false ORDER BY RANDOM() LIMIT 1")
    url = cursor.fetchone()
    return url

def update_image_usage(url):
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("UPDATE images SET used=true WHERE url=?", (url,))
    connection.commit()

def inlinequery(update, context):
    query = update.inline_query.query
    url = get_image_urls()
    if url:
        results = [
            InlineQueryResultArticle(
                id=url[0],
                title="Image",
                input_message_content=InputTextMessageContent(url[0]),
                thumb_url=url[0]
            )
        ]
        update_image_usage(url[0])
        update.inline_query.answer(results)

def main():
    updater = Updater(token=os.environ['TELEGRAM_BOT_TOKEN'], use_context=True)
    dp = updater.dispatcher
    dp.add_handler(InlineQueryHandler(inlinequery))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
