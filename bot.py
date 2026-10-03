import re
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import database
import config
import helius

WALLET_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

def is_admin(message: Message) -> bool:
    return bool(message.from_user and message.from_user.id == config.ADMIN_ID)

async def reply(message: Message, text: str):
    await message.answer(text)

async def cmd_start(message: Message):
    if not is_admin(message):
        return
    await reply(
        message,
        "Solana wallet tracker\\n\\n"
        "/add wallet_address wallet_name\\n"
        "/remove wallet_address\\n"
        "/set_chat chat_id"
    )

async def cmd_add(message: Message, reconcile):
    if not is_admin(message):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) != 3:
        await reply(message, "Usage: /add wallet_address wallet_name")
        return

    address, name = parts[1].strip(), parts[2].strip()
    if not WALLET_RE.fullmatch(address):
        await reply(message, "Invalid Solana wallet address.")
        return

    await database.add_wallet(address, name)
    try:
        await reconcile()
        await reply(message, "Wallet added.")
    except Exception as e:
        await database.remove_wallet(address)
        await reply(message, f"Could not update Helius: {e}")

async def cmd_remove(message: Message, reconcile):
    if not is_admin(message):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        await reply(message, "Usage: /remove wallet_address")
        return

    address = parts[1].strip()
    if not WALLET_RE.fullmatch(address):
        await reply(message, "Invalid Solana wallet address.")
        return

    removed = await database.remove_wallet(address)
    if not removed:
        await reply(message, "Wallet not found.")
        return

    try:
        await reconcile()
        await reply(message, "Wallet removed.")
    except Exception as e:
        await reply(message, f"Wallet removed locally, but Helius update failed: {e}")

async def cmd_set_chat(message: Message):
    if not is_admin(message):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        await reply(message, "Usage: /set_chat chat_id")
        return
    chat_id = parts[1].strip()
    try:
        int(chat_id)
    except ValueError:
        await reply(message, "Chat ID must be numeric.")
        return
    await database.set_setting("destination_chat_id", chat_id)
    await reply(message, "Destination chat saved.")

def build_dispatcher(reconcile):
    dp = Dispatcher()

    dp.message.register(cmd_start, Command("start"))
    dp.message.register(lambda m: cmd_add(m, reconcile), Command("add"))
    dp.message.register(lambda m: cmd_remove(m, reconcile), Command("remove"))
    dp.message.register(cmd_set_chat, Command("set_chat"))

    return dp
