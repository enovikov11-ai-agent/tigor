import uuid
import json
import time
import faiss
import openai
import openai_api_key
import numpy as np
from tg_secrets import TG_TOKEN, is_allowed
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, InlineQueryHandler, MessageHandler, Filters

def search(query):
    query_vector = np.array(openai.Embedding.create(input=[query], model="text-embedding-ada-002")['data'][0]['embedding'])
    scores, ids = index.search(query_vector.reshape(1, -1), 5)

    return "\n\n".join([results[id] for id in list(ids[0])])

def log(query, uid, type):
    with open("query.log", "a") as f:
        data = {"query": query, "uid": uid, "unixtime": time.time(), "type": type}
        f.write(json.dumps(data, ensure_ascii=False) + '\n')

def payload(query, uid, type):
    return f"Запрос: {query}\n\n" + search(query)

def text_message(update, context):
    log(str(update.message.text), int(update.effective_user.id), "text")

    if not is_allowed(update.effective_user.id):
        return 
    
    update.message.reply_text(payload(str(update.message.text), int(update.effective_user.id), "text"))

def inline_query(update, context):
    log(str(update.inline_query.query), int(update.effective_user.id), "text")

    if not is_allowed(update.effective_user.id):
        return 
    
    if update.inline_query.query == '':
        return
    
    result = payload(str(update.inline_query.query), int(update.effective_user.id), "inline")

    update.inline_query.answer([
        InlineQueryResultArticle(
            id = str(uuid.uuid4())[:64] ,
            title = 'title',
            input_message_content = InputTextMessageContent(result)
        )
    ])

index = faiss.read_index("./model/z1000.faiss")
results = json.load(open('./model/z1000.json', 'r'))

updater = Updater(token=TG_TOKEN)
dispatcher = updater.dispatcher

dispatcher.add_handler(InlineQueryHandler(inline_query))
dispatcher.add_handler(MessageHandler(Filters.text, text_message))

updater.start_polling()
updater.idle()
