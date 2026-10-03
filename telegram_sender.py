from telethon import TelegramClient
from telethon.sessions import StringSession
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION_STRING

class TelegramSender:
    def __init__(self):
        self.client = TelegramClient(
            StringSession(TELEGRAM_SESSION_STRING),
            TELEGRAM_API_ID,
            TELEGRAM_API_HASH,
        )

    async def start(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            raise RuntimeError("TELEGRAM_SESSION_STRING is not authorized.")
        me = await self.client.get_me()
        print(f"Telegram user connected: @{me.username or me.id}")

    async def send_ca(self, chat_id: str, mint: str):
        if not chat_id:
            raise RuntimeError("Destination chat is not set.")
        # No formatting, no caption, no extra text.
        await self.client.send_message(
            int(chat_id),
            mint,
            parse_mode=None,
            link_preview=False,
        )

    async def stop(self):
        await self.client.disconnect()
