import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession

async def main():
    api_id = int(input("Telegram API ID: ").strip())
    api_hash = input("Telegram API HASH: ").strip()

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start()
    print("\nTELEGRAM_SESSION_STRING=")
    print(client.session.save())
    print("\nKeep this string private. Anyone with it can access the Telegram session.")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
