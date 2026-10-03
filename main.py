import asyncio
import logging
from aiohttp import web
from aiogram import Bot
import config
import database
import helius
from bot import build_dispatcher
from detector import extract_bought_mints
from telegram_sender import TelegramSender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

class App:
    def __init__(self):
        self.bot = Bot(config.BOT_TOKEN)
        self.sender = TelegramSender()
        self.base_url = config.PUBLIC_BASE_URL
        self.webhook_id = None
        self.queue = asyncio.Queue()
        self.worker_task = None

    async def reconcile(self):
        addresses = await database.wallet_addresses()
        self.webhook_id = await helius.reconcile_webhook(addresses, self.base_url)
        logging.info("Helius webhook reconciled: %s | wallets=%d", self.webhook_id, len(addresses))

    async def handle_helius(self, request: web.Request):
        expected = f"Bearer {config.WEBHOOK_SECRET}"
        if request.headers.get("Authorization") != expected:
            return web.json_response({"error": "unauthorized"}, status=401)

        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"error": "invalid json"}, status=400)

        events = payload if isinstance(payload, list) else [payload]

        for tx in events:
            signature = tx.get("signature")
            if not signature:
                continue

            # Helius can retry. Persist signature before processing.
            if not await database.mark_processed(signature):
                continue

            wallets = set(await database.wallet_addresses())
            pairs = extract_bought_mints(tx, wallets)

            for wallet, mint in pairs:
                await self.queue.put((wallet, mint, signature))

        # Always ACK valid authenticated deliveries quickly.
        return web.json_response({"received": len(events)})

    async def worker(self):
        while True:
            wallet, mint, signature = await self.queue.get()
            try:
                destination = await database.get_setting("destination_chat_id")
                if not destination:
                    logging.warning("Buy detected but destination chat is not set: %s", mint)
                    continue

                # The queue is processed by one worker, so check + send + record
                # is serialized. Record only after Telegram confirms the send;
                # otherwise a temporary Telegram failure would permanently lose the CA.
                if await database.has_sent_ca(mint):
                    logging.info("Duplicate CA ignored: %s", mint)
                    continue

                try:
                    await self.sender.send_ca(destination, mint)
                    if not await database.claim_ca(mint, signature, wallet):
                        # Another process should not normally exist on a Railway
                        # Volume-backed singleton service, but never resend here.
                        logging.warning("CA became a duplicate after send: %s", mint)
                        continue
                    logging.info("Sent CA: %s", mint)
                except Exception:
                    logging.exception("Telegram send failed for CA: %s", mint)
            except Exception:
                logging.exception("Worker error")
            finally:
                self.queue.task_done()

    async def health(self, request):
        return web.json_response({"ok": True})

    async def start(self):
        await database.init_db()
        await self.sender.start()

        # PUBLIC_BASE_URL is required because Helius must reach this service.
        if not config.PUBLIC_BASE_URL:
            logging.warning(
                "PUBLIC_BASE_URL is not set. Set it to the Railway HTTPS domain, "
                "e.g. https://your-service.up.railway.app"
            )

        if config.PUBLIC_BASE_URL:
            await self.reconcile()

        self.worker_task = asyncio.create_task(self.worker())

        app = web.Application()
        app.router.add_get("/health", self.health)
        app.router.add_post(config.WEBHOOK_PATH, self.handle_helius)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", config.PORT)
        await site.start()

        logging.info("HTTP server listening on 0.0.0.0:%d", config.PORT)

        dp = build_dispatcher(self.reconcile)
        try:
            await dp.start_polling(self.bot)
        finally:
            await self.bot.session.close()
            await self.sender.stop()
            if self.worker_task:
                self.worker_task.cancel()
            await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(App().start())
