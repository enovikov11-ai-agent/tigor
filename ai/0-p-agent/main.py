import subprocess, functools, os
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

_halted = False
_timeout = 4 * 60

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GIT_PASS = os.getenv("GIT_PASS")
WEB_URL = os.getenv("WEB_URL")

WORK_DIR = "/work"
HALT_FLAG_FILE = "/tmp/p-agent_halted"

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
if not ADMIN_TELEGRAM_ID:
    raise RuntimeError("ADMIN_TELEGRAM_ID is required")
if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY is required")
if not GIT_PASS:
    raise RuntimeError("GIT_PASS is required")
if not WEB_URL:
    raise RuntimeError("WEB_URL is required")


def require_auth(func):
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        global _halted

        if not _halted and os.path.exists(HALT_FLAG_FILE):
            _halted = True
        
        if _halted:
            return
        if not update.effective_user or update.effective_user.id != ADMIN_TELEGRAM_ID:
            return
        if update.effective_chat.type != "private":
            return
        return await func(update, context)
    return wrapper


@require_auth
async def handle_settimeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _timeout
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(f"Current timeout: {_timeout}s\nUsage: /settimeout <seconds>")
        return
    _timeout = int(context.args[0])
    await update.message.reply_text(f"Timeout set to {_timeout}s")


@require_auth
async def handle_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text.split()[0].lstrip("/").split("@")[0]
    payload = " ".join(context.args) if context.args else ""
    if not payload:
        await update.message.reply_text(f"Usage: /{command} <task description>")
        return

    payload = "You are autonomous agent, please not only make a plan but execute it. " + payload

    timeout = _timeout
    orig_id = update.message.message_id
    ts = int(datetime.now().timestamp())
    log_path = f"{WORK_DIR}/{ts}.log"
    os.makedirs(WORK_DIR, exist_ok=True)
    status_msg = await update.message.reply_text(f"Starting agent, timeout {timeout}s\nless +F {log_path}", reply_to_message_id=orig_id)

    env = os.environ | {"TELEGRAM_BOT_TOKEN": "", "COMMAND": command, "PAYLOAD": payload}

    try:
        result = subprocess.run(f"bash agent-task.sh 2>&1 | ts '[%H:%M]' | tee {log_path}", shell=True, stdout=subprocess.PIPE, text=True, timeout=timeout, check=True, env=env)
        agent_output = result.stdout
    except subprocess.CalledProcessError as e:
        agent_output = (e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout or "") + "\nTask failed."
    except subprocess.TimeoutExpired as e:
        agent_output = (e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout or "") + "\nTimed out."

    agent_output = agent_output.replace(TELEGRAM_BOT_TOKEN, "[MASKED]").replace(ANTHROPIC_API_KEY, "[MASKED]").replace(GIT_PASS, "[MASKED]")
    await status_msg.edit_text("\n".join(agent_output[-4000:].splitlines()[-30:]))


@require_auth
async def handle_halt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _halted
    _halted = True

    try:
        with open(HALT_FLAG_FILE, 'w') as f:
            f.write('halted')
    except Exception:
        pass

    await update.message.reply_text("Bot halted. Restart required to resume.")


async def on_startup(app):
    await app.bot.set_my_commands([
        BotCommand("cd", "cd Code"),
        BotCommand("qwen", "Qwen3-Next 80B"),
        BotCommand("minimax", "MiniMax M2.5"),
        BotCommand("halt", "Emergency stop"),
        BotCommand("settimeout", "Set job timeout (seconds)"),
    ])
    await app.bot.send_message(chat_id=ADMIN_TELEGRAM_ID, text="Bot started.")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(on_startup).build()
    app.add_handler(CommandHandler("cd", handle_agent))
    app.add_handler(CommandHandler("qwen", handle_agent))
    app.add_handler(CommandHandler("minimax", handle_agent))
    app.add_handler(CommandHandler("halt", handle_halt))
    app.add_handler(CommandHandler("settimeout", handle_settimeout))
    app.run_polling(allowed_updates=["message"])
