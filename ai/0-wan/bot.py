import argparse
import asyncio
import gc
import logging
import os
from pathlib import Path

from generate import generate
from telegram import BotCommand, Message, Update
from telegram.constants import ChatAction
from telegram.ext import Application, ApplicationBuilder, ContextTypes, MessageHandler, filters

ALLOWED_CHAT_IDS = {
    int(chat_id.strip())
    for chat_id in os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "").split(",")
    if chat_id.strip()
}

BASE_SEED = 42

T2V_CKPT_DIR = "/ssd/internet/huggingface.co/Wan-AI/Wan2.2-T2V-A14B/"
I2V_CKPT_DIR = "/ssd/internet/huggingface.co/Wan-AI/Wan2.2-I2V-A14B/"

TMP_DIR = Path("/tmp/tg_wan_bot")

DEFAULT_WIDTH = 832
DEFAULT_HEIGHT = 480
DEFAULT_FRAMES = 81
DEFAULT_STEPS = 20

ALLOWED_SIZES = {
    (720, 1280),
    (1280, 720),
    (480, 832),
    (832, 480),
    (704, 1280),
    (1280, 704),
    (1024, 704),
    (704, 1024),
}

ALLOWED_FRAMES = {49, 81, 113, 145, 177}
ALLOWED_STEPS = {20, 40, 60}
ALLOWED_LETTERS = {"w", "h", "f", "s"}

DEFAULT_SAMPLE_GUIDE_SCALE = 5.0
DEFAULT_SAMPLE_SHIFT = 12.0
DEFAULT_OFFLOAD_MODEL = False
CONVERT_MODEL_DTYPE = True

INVITE_TEXT = "Ask an administrator for access."

HELP_TEXT = (
    "Usage: /gen[number+letter...] prompt\n"
    "\n"
    "Examples:\n"
    "/gen prompt\n"
    "/gen832w480h prompt\n"
    "/gen40s prompt\n"
    "/gen832w480h40s prompt\n"
    "\n"
    "Allowed letters:\n"
    "w - width\n"
    "h - height\n"
    "f - frames\n"
    "s - steps\n"
    "\n"
    "Allowed sizes:\n"
    "720x1280, 1280x720, 480x832, 832x480, 704x1280, 1280x704, 1024x704, 704x1024\n"
    "\n"
    "Allowed frames:\n"
    "49, 81, 113, 145, 177\n"
    "\n"
    "Allowed steps:\n"
    "20, 40, 60\n"
    "\n"
    "Defaults:\n"
    "832x480, 81 frames, 20 steps\n"
    "\n"
    "Attach or reply to a JPG/JPEG image for image-to-video. Otherwise text-to-video is used."
)

generation_lock = asyncio.Lock()
last_model_name: str | None = None


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def allowed(update: Update) -> bool:
    chat = update.effective_chat
    return chat is not None and chat.id in ALLOWED_CHAT_IDS


def is_forwarded(message: Message | None) -> bool:
    if message is None:
        return False

    fields = (
        "forward_origin",
        "forward_date",
        "forward_from",
        "forward_from_chat",
        "forward_sender_name",
        "forward_signature",
    )

    return any(getattr(message, field, None) is not None for field in fields)


def parse_command(message: Message) -> tuple[str, str]:
    text = (message.text or message.caption or "").strip()
    if not text.startswith("/"):
        return "", ""

    parts = text.split(maxsplit=1)
    command = parts[0][1:].split("@", 1)[0]
    prompt = parts[1].strip() if len(parts) > 1 else ""
    return command, prompt


def help_answer(reason: str | None = None) -> str:
    if reason:
        return f"{reason}\n\n{HELP_TEXT}"

    return HELP_TEXT


def parse_gen_params(command: str) -> tuple[dict[str, int] | None, str | None]:
    if not command.startswith("gen"):
        return None, "Unsupported command."

    suffix = command[3:]
    width = DEFAULT_WIDTH
    height = DEFAULT_HEIGHT
    frames = DEFAULT_FRAMES
    steps = DEFAULT_STEPS

    i = 0
    while i < len(suffix):
        start = i

        while i < len(suffix) and suffix[i].isdigit():
            i += 1

        if start == i:
            bad = suffix[i] if i < len(suffix) else ""
            if bad:
                return None, f"Invalid command: expected number before '{bad}'."
            return None, "Invalid command."

        if i >= len(suffix):
            return None, "Invalid command: number must be followed by one of w, h, f, s."

        value = int(suffix[start:i])
        letter = suffix[i].lower()
        i += 1

        if letter not in ALLOWED_LETTERS:
            return None, f"Invalid command: unknown letter '{letter}'."

        if letter == "w":
            width = value
        elif letter == "h":
            height = value
        elif letter == "f":
            frames = value
        elif letter == "s":
            steps = value

    if (width, height) not in ALLOWED_SIZES:
        return None, f"Invalid size: {width}x{height}."

    if frames not in ALLOWED_FRAMES:
        return None, f"Invalid frames value: {frames}."

    if steps not in ALLOWED_STEPS:
        return None, f"Invalid steps value: {steps}."

    return {
        "width": width,
        "height": height,
        "frames": frames,
        "steps": steps,
    }, None


def gen_spec(params: dict[str, int], kind: str) -> dict[str, object]:
    if kind == "i2v":
        return {
            "kind": "i2v",
            "task": "i2v-A14B",
            "size": f"{params['width']}*{params['height']}",
            "width": params["width"],
            "height": params["height"],
            "frames": params["frames"],
            "steps": params["steps"],
            "ckpt_dir": I2V_CKPT_DIR,
        }

    return {
        "kind": "t2v",
        "task": "t2v-A14B",
        "size": f"{params['width']}*{params['height']}",
        "width": params["width"],
        "height": params["height"],
        "frames": params["frames"],
        "steps": params["steps"],
        "ckpt_dir": T2V_CKPT_DIR,
    }


def reply_text_without_command(message: Message) -> str:
    reply = message.reply_to_message
    if reply is None or is_forwarded(reply):
        return ""

    text = (reply.text or reply.caption or "").strip()
    if not text:
        return ""

    if not text.startswith("/"):
        return text

    parts = text.split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""


def get_prompt(message: Message, prompt: str) -> str:
    return prompt or reply_text_without_command(message)


def user_label(update: Update) -> str:
    user = update.effective_user
    if user is None:
        return "unknown @unknown (uid=unknown)"

    name = user.full_name or user.first_name or "unknown"
    username = f"@{user.username}" if user.username else "@unknown"
    return f"{name} {username} (uid={user.id})"


def has_media(message: Message | None) -> bool:
    return bool(message and not is_forwarded(message) and (message.photo or message.document))


def is_jpg(message: Message | None) -> bool:
    if message is None or is_forwarded(message):
        return False

    if message.photo:
        return True

    doc = message.document
    if doc is None:
        return False

    name = (doc.file_name or "").lower()
    mime = (doc.mime_type or "").lower()

    return name.endswith((".jpg", ".jpeg")) or mime in {"image/jpeg", "image/jpg"}


def image_message(message: Message) -> Message | None:
    if is_jpg(message):
        return message

    if is_jpg(message.reply_to_message):
        return message.reply_to_message

    return None


def media_message(message: Message) -> Message | None:
    if has_media(message):
        return message

    if has_media(message.reply_to_message):
        return message.reply_to_message

    return None


async def save_image(message: Message, context: ContextTypes.DEFAULT_TYPE, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id
    else:
        raise RuntimeError("No image found")

    tg_file = await context.bot.get_file(file_id)
    await tg_file.download_to_drive(custom_path=str(path))

    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError(f"Downloaded image is missing or empty: {path}")


def size_label(spec: dict[str, object]) -> str:
    return str(spec["size"]).replace("*", "x")


def mode_label(spec: dict[str, object]) -> str:
    if spec["kind"] == "i2v":
        return "image-to-video"

    return "text-to-video"


def chosen_values_text(prefix: str, spec: dict[str, object]) -> str:
    return (
        f"{prefix}\n"
        f"Mode: {mode_label(spec)}\n"
        f"Model: {spec['task']}\n"
        f"Size: {size_label(spec)}\n"
        f"Frames: {spec['frames']}\n"
        f"Steps: {spec['steps']}"
    )


def caption(update: Update, spec: dict[str, object]) -> str:
    return (
        f"Generated for {user_label(update)}\n"
        f"Used: {spec['task']}, size {size_label(spec)}, {spec['frames']} frames, {spec['steps']} steps\n"
        f"Mode: {mode_label(spec)}\n\n"
        f"{INVITE_TEXT}"
    )


def wan_args(
    spec: dict[str, object],
    prompt: str,
    output_path: Path,
    image_path: Path | None,
    offload_model: bool,
) -> argparse.Namespace:
    return argparse.Namespace(
        task=spec["task"],
        size=spec["size"],
        frame_num=spec["frames"],
        ckpt_dir=spec["ckpt_dir"],
        offload_model=offload_model,
        ulysses_size=1,
        t5_fsdp=False,
        t5_cpu=False,
        dit_fsdp=False,
        save_file=str(output_path),
        prompt=prompt,
        use_prompt_extend=False,
        prompt_extend_method="local_qwen",
        prompt_extend_model=None,
        prompt_extend_target_lang="zh",
        base_seed=BASE_SEED,
        image=str(image_path) if image_path else None,
        sample_solver="unipc",
        sample_steps=spec["steps"],
        sample_shift=DEFAULT_SAMPLE_SHIFT,
        sample_guide_scale=DEFAULT_SAMPLE_GUIDE_SCALE,
        convert_model_dtype=CONVERT_MODEL_DTYPE,
        src_root_path=None,
        refert_num=77,
        replace_flag=False,
        use_relighting_lora=False,
        num_clip=None,
        audio=None,
        enable_tts=False,
        tts_prompt_audio=None,
        tts_prompt_text=None,
        tts_text=None,
        pose_video=None,
        start_from_ref=False,
        infer_frames=80,
    )


def cleanup_cuda() -> None:
    try:
        gc.collect()
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except Exception:
        logging.exception("CUDA cleanup failed")


async def chat_action_loop(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    stop: asyncio.Event,
) -> None:
    while not stop.is_set():
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
        except Exception:
            logging.exception("send_chat_action failed")

        try:
            await asyncio.wait_for(stop.wait(), timeout=4)
        except asyncio.TimeoutError:
            pass


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global last_model_name

    if not allowed(update):
        return

    message = update.effective_message
    if message is None:
        return

    if is_forwarded(message):
        return

    command, raw_prompt = parse_command(message)
    if not command:
        return

    params, parse_error = parse_gen_params(command)
    if parse_error or params is None:
        await message.reply_text(help_answer(parse_error))
        return

    prompt = get_prompt(message, raw_prompt)
    if not prompt:
        await message.reply_text(help_answer("Missing prompt."))
        return

    any_media = media_message(message)
    jpg = image_message(message)

    if any_media is not None and jpg is None:
        await message.reply_text(help_answer("Invalid image: only JPG/JPEG is accepted."))
        return

    kind = "i2v" if jpg is not None else "t2v"
    spec = gen_spec(params, kind)

    image_path: Path | None = None
    if kind == "i2v":
        image_path = TMP_DIR / f"wan_{message.chat_id}_{message.message_id}_input.jpg"

    TMP_DIR.mkdir(parents=True, exist_ok=True)

    output_path = TMP_DIR / (
        f"wan_{message.chat_id}_{message.message_id}_"
        f"{spec['kind']}_{spec['width']}x{spec['height']}_f{spec['frames']}_s{spec['steps']}.mp4"
    )

    stop = asyncio.Event()
    action_task = asyncio.create_task(chat_action_loop(context, message.chat_id, stop))

    try:
        output_path.unlink(missing_ok=True)

        if image_path is not None:
            image_path.unlink(missing_ok=True)
            await save_image(jpg, context, image_path)

        async with generation_lock:
            model_name = str(spec["task"])
            switched = last_model_name is not None and last_model_name != model_name
            offload = DEFAULT_OFFLOAD_MODEL

            if switched:
                cleanup_cuda()
                offload = True

            await message.reply_text(chosen_values_text("Generation started", spec))

            args = wan_args(spec, prompt, output_path, image_path, offload)
            await asyncio.to_thread(generate, args)
            last_model_name = model_name

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(f"Generation finished but output is missing: {output_path}")

        with output_path.open("rb") as video:
            await message.reply_video(
                video=video,
                caption=caption(update, spec),
                supports_streaming=True,
                read_timeout=300,
                write_timeout=300,
                connect_timeout=60,
                pool_timeout=60,
            )

    except Exception:
        logging.exception("Generation failed")
        await message.reply_text("Generation failed")

    finally:
        stop.set()

        try:
            await action_task
        except Exception:
            logging.exception("chat_action_task failed")

        try:
            output_path.unlink(missing_ok=True)
        except Exception:
            logging.exception("Failed to remove output file: %s", output_path)

        try:
            if image_path is not None:
                image_path.unlink(missing_ok=True)
        except Exception:
            logging.exception("Failed to remove input image file: %s", image_path)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.exception("Unhandled bot error", exc_info=context.error)


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            BotCommand("gen", "Generate"),
        ]
    )


def main() -> None:
    setup_logging()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN")

    application = (
        ApplicationBuilder()
        .token(token)
        .post_init(post_init)
        .build()
    )

    application.add_handler(MessageHandler(filters.ALL, handle_message))
    application.add_error_handler(error_handler)

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
