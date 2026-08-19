from telegram.ext import Application, MessageHandler, CallbackContext
from telegram.ext.filters import ALL
from telegram import Update
import datetime, hashlib, base64, hmac, os


keys = {"tg": os.getenv("TIGOR_TG_SECRET")}

if not keys["tg"] or len(keys["tg"]) < 16:
    raise Exception("Key not found TIGOR_TG_SECRET")


def sign_token_v1(user_id: str, priority: int = 1, max_daily_messages: int = 100, max_tokens: int = 4096, valid_days: int = 7, authority: str = "tg"):
    values = [user_id, priority, max_daily_messages, max_tokens, authority]
    user_id, priority, max_daily_messages, max_tokens, authority = [str(value).replace("|", "_") for value in values]

    valid_until = (datetime.date.today() + datetime.timedelta(days=valid_days)).strftime("%Y-%m-%d")
    version = "v1"

    message = user_id + "|" + priority + "|" + max_daily_messages + "|" + max_tokens + "|" + valid_until + "|" + version + "|" + authority

    signature_raw = hmac.new(keys[authority].encode(), message.encode(), hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(signature_raw).decode()

    return "Authorization: Bearer " + message + "|" + signature


async def message_handler(update: Update, context: CallbackContext) -> None:
    token = sign_token_v1(f"tg_{update.effective_user.id}")
    user_id, priority, max_daily_messages, max_tokens, valid_until, version, authority, signature = token.replace("Authorization: Bearer ", "").split("|")
    text = f"""Ваш токен

{token}

User ID: {user_id}
Приоритет: {priority} (больше - выше приоритет)
Лимит сообщений в день: {max_daily_messages}
Лимит токенов на сообщение: {max_tokens}
Токен действителен до: {valid_until}
Версия токена: {version}
Токен выдан: {authority}
Цифровая подпись: {signature}"""

    await update.message.reply_text(text)


application: Application = Application.builder().token(os.getenv("TIGOR_TG_API_KEY")).build()
application.add_handler(MessageHandler(ALL, message_handler))
application.run_polling()
