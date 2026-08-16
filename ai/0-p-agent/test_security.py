"""Tests for security features: require_auth decorator and halt behaviour."""
import asyncio
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock

# Mock telegram before importing main so the package is not required
sys.modules.setdefault("telegram", MagicMock())
sys.modules.setdefault("telegram.ext", MagicMock())

# Set required env vars before importing main (checked at module level)
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("ADMIN_TELEGRAM_ID", "12345")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("GIT_PASS", "test-pass")
os.environ.setdefault("WEB_URL", "http://test.com/")

import main  # safe to import now that app startup is guarded by __main__

ADMIN_TELEGRAM_ID = main.ADMIN_TELEGRAM_ID


# --- Helpers ---

def make_update(user_id=None, chat_type="private"):
    update = MagicMock()
    if user_id is None:
        update.effective_user = None
    else:
        update.effective_user.id = user_id
    update.effective_chat.type = chat_type
    update.message.reply_text = AsyncMock()
    update.message.message_id = 1
    return update


def run(coro):
    return asyncio.run(coro)


def guarded(handler=None):
    inner = handler or AsyncMock()
    return main.require_auth(inner), inner


# --- Reset halt state between tests ---

@pytest.fixture(autouse=True)
def reset_halt():
    main._halted = False
    if os.path.exists(main.HALT_FLAG_FILE):
        os.remove(main.HALT_FLAG_FILE)
    yield
    main._halted = False
    if os.path.exists(main.HALT_FLAG_FILE):
        os.remove(main.HALT_FLAG_FILE)


# --- require_auth: access control ---

def test_allows_admin_in_private_chat():
    decorated, inner = guarded()
    run(decorated(make_update(user_id=ADMIN_TELEGRAM_ID, chat_type="private"), MagicMock()))
    inner.assert_called_once()


def test_blocks_non_admin_user():
    decorated, inner = guarded()
    run(decorated(make_update(user_id=ADMIN_TELEGRAM_ID + 1, chat_type="private"), MagicMock()))
    inner.assert_not_called()


def test_blocks_missing_user():
    decorated, inner = guarded()
    run(decorated(make_update(user_id=None, chat_type="private"), MagicMock()))
    inner.assert_not_called()


def test_blocks_group_chat():
    decorated, inner = guarded()
    run(decorated(make_update(user_id=ADMIN_TELEGRAM_ID, chat_type="group"), MagicMock()))
    inner.assert_not_called()


def test_blocks_supergroup_chat():
    decorated, inner = guarded()
    run(decorated(make_update(user_id=ADMIN_TELEGRAM_ID, chat_type="supergroup"), MagicMock()))
    inner.assert_not_called()


# --- require_auth: halt flag (in-memory) ---

def test_blocks_when_halted_in_memory():
    main._halted = True
    decorated, inner = guarded()
    run(decorated(make_update(user_id=ADMIN_TELEGRAM_ID, chat_type="private"), MagicMock()))
    inner.assert_not_called()


def test_halt_blocks_even_admin():
    main._halted = True
    decorated, inner = guarded()
    run(decorated(make_update(user_id=ADMIN_TELEGRAM_ID, chat_type="private"), MagicMock()))
    inner.assert_not_called()


# --- require_auth: halt flag (file) ---

def test_blocks_when_halt_file_exists():
    with open(main.HALT_FLAG_FILE, "w") as f:
        f.write("halted")
    decorated, inner = guarded()
    run(decorated(make_update(user_id=ADMIN_TELEGRAM_ID, chat_type="private"), MagicMock()))
    inner.assert_not_called()


def test_halt_file_promotes_to_memory_flag():
    with open(main.HALT_FLAG_FILE, "w") as f:
        f.write("halted")
    decorated, inner = guarded()
    run(decorated(make_update(user_id=ADMIN_TELEGRAM_ID, chat_type="private"), MagicMock()))
    assert main._halted is True


def test_halt_is_one_way_after_file_removed():
    """Once the memory flag is set from a file, removing the file doesn't un-halt."""
    with open(main.HALT_FLAG_FILE, "w") as f:
        f.write("halted")
    decorated, inner = guarded()
    update = make_update(user_id=ADMIN_TELEGRAM_ID, chat_type="private")
    run(decorated(update, MagicMock()))   # file detected → memory flag set
    os.remove(main.HALT_FLAG_FILE)
    decorated2, inner2 = guarded()
    run(decorated2(update, MagicMock()))  # memory flag still blocks
    inner2.assert_not_called()


# --- handle_halt ---

def test_handle_halt_sets_memory_flag():
    update = make_update(user_id=ADMIN_TELEGRAM_ID, chat_type="private")
    run(main.handle_halt(update, MagicMock()))
    assert main._halted is True


def test_handle_halt_creates_flag_file():
    update = make_update(user_id=ADMIN_TELEGRAM_ID, chat_type="private")
    run(main.handle_halt(update, MagicMock()))
    assert os.path.exists(main.HALT_FLAG_FILE)


def test_handle_halt_sends_confirmation():
    update = make_update(user_id=ADMIN_TELEGRAM_ID, chat_type="private")
    run(main.handle_halt(update, MagicMock()))
    update.message.reply_text.assert_called_once()


def test_handle_halt_blocks_subsequent_commands():
    update = make_update(user_id=ADMIN_TELEGRAM_ID, chat_type="private")
    run(main.handle_halt(update, MagicMock()))
    decorated, inner = guarded()
    run(decorated(update, MagicMock()))
    inner.assert_not_called()
