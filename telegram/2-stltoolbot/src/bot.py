from telegram.ext import Application, MessageHandler, filters
from telegram import InputFile
from asyncio import Lock
import tempfile
import random
import socket
import json
import sys
import os
import re

dir = os.path.dirname(os.path.abspath(__file__))
if dir not in sys.path:
    sys.path.append(dir)

from tools import init, build_text


def rpc_connect():
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect("./jsonrpc.sock")


def rpc_call(method, *args):
    sock.sendall(json.dumps({"jsonrpc": "2.0", "method": method,
                 "params": args, "id": random.randint(0, 2**31 - 1)}).encode())

    return json.loads(sock.recv(16384).decode())['result']


async def on_text(update, context):
    async with lock:
        if re.match(valid_text_re, update.message.text):
            with tempfile.NamedTemporaryFile(suffix='.stl', delete=True) as tmp:
                build_text(update.message.text, tmp.name)
                with open(tmp.name, "rb") as file:
                    await context.bot.send_document(
                        chat_id=update.effective_chat.id,
                        document=InputFile(file, update.message.text + ".stl")
                    )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Связь с автором - @enovikov11. Текст не прошел валидацию, см https://github.com/enovikov11/STLtoolbot"
            )


global sock

init("//RobotoMono-Bold.ttf")

valid_text_re = r"^[ \nа-яёА-ЯЁa-zA-Z0-9!@#$%^&*()_+\-=\[\]{}|\\;:\"\',.<>\/?]{1,300}$"
lock = Lock()

app = Application.builder().token(os.getenv("API_KEY")).build()
app.add_handler(MessageHandler(filters.TEXT, on_text))
app.run_polling()
