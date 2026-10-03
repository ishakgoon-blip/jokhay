import os
from pathlib import Path

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

HELIUS_API_KEY = os.environ["HELIUS_API_KEY"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]

TELEGRAM_API_ID = int(os.environ["TELEGRAM_API_ID"])
TELEGRAM_API_HASH = os.environ["TELEGRAM_API_HASH"]
TELEGRAM_SESSION_STRING = os.environ["TELEGRAM_SESSION_STRING"]

PORT = int(os.getenv("PORT", "8080"))
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "tracker.db"

WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/helius/webhook")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
if not PUBLIC_BASE_URL:
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if railway_domain:
        PUBLIC_BASE_URL = "https://" + railway_domain.rstrip("/")

DEFAULT_QUOTES = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
    "So11111111111111111111111111111111111111112",    # WSOL
}
QUOTE_MINTS = {
    x.strip() for x in os.getenv("QUOTE_MINTS", ",".join(DEFAULT_QUOTES)).split(",")
    if x.strip()
}

# The app refuses to guess a public URL from headers. Set this on Railway if needed.
def webhook_url(request_base_url: str | None = None) -> str:
    base = PUBLIC_BASE_URL or (request_base_url or "").rstrip("/")
    if not base:
        raise RuntimeError(
            "PUBLIC_BASE_URL is not set. Set it to your Railway HTTPS domain."
        )
    return base + WEBHOOK_PATH
