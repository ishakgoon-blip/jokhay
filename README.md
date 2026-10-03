# Solana Wallet Tracker — Railway

Minimal Solana wallet tracker with:

- Telegram **bot** for admin commands only
- Helius Enhanced `SWAP` webhooks for real-time detection
- Telegram **user account** (Telethon) for sending the CA/mint only
- Global CA deduplication
- SQLite persistence
- Railway Volume support
- Dynamic Helius webhook account list when wallets are added/removed

## Commands

```text
/start
/add WALLET_ADDRESS WALLET_NAME
/remove WALLET_ADDRESS
/set_chat CHAT_ID
```

`/add` and `/remove` update the Helius webhook automatically.

## What counts as a buy?

The tracker accepts a `SWAP` only when:

1. The tracked wallet receives an SPL token in the swap.
2. The received mint is not a configured quote/settlement mint.
3. The wallet is spending native SOL or one of the configured quote SPL mints.

This intentionally avoids treating ordinary token transfers as buys and avoids treating a normal token sale as a buy.

Default quote SPL mints:

- USDC: `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`
- USDT: `Es9vMFrzaCERmJfrF4H2FYD4vKf4g1Y9j7Q1dZq8n1o`
- WSOL: `So11111111111111111111111111111111111111112`

You can override them with `QUOTE_MINTS`.

## Environment variables

Required:

```text
BOT_TOKEN=
ADMIN_ID=
HELIUS_API_KEY=

TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_SESSION_STRING=

WEBHOOK_SECRET=
```

Recommended:

```text
PORT=8080
DATA_DIR=/data
QUOTE_MINTS=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v,Es9vMFrzaCERmJfrF4H2FYD4vKf4g1Y9j7Q1dZq8n1o,So11111111111111111111111111111111111111112
WEBHOOK_PATH=/helius/webhook
```

`TELEGRAM_SESSION_STRING` is the login credential for the Telegram user account. Keep it secret.

## First local setup

1. Create a Telegram bot with BotFather and get `BOT_TOKEN`.
2. Get `ADMIN_ID` from your Telegram account.
3. Get a Helius API key.
4. Get Telegram `api_id` and `api_hash` from `my.telegram.org`.
5. Generate a Telethon StringSession:

```bash
pip install Telethon
python generate_session.py
```

Follow the prompts and copy the printed session string into `TELEGRAM_SESSION_STRING`.

6. Install:

```bash
pip install -r requirements.txt
```

7. Start:

```bash
python main.py
```

For local Helius webhook testing, the server must have a public HTTPS URL. Railway is the simplest deployment target.

## Railway deployment

Push this folder to GitHub or deploy the folder directly with Railway.

Set the variables above in Railway.

Then:

1. Deploy the service.
2. Generate a Railway public domain under Networking.
3. Add a Railway Volume.
4. Mount it at:

```text
/data
```

The app stores `/data/tracker.db`.

Railway's filesystem outside a Volume is ephemeral; the Volume is what makes SQLite survive redeploys/restarts.

5. Restart/redeploy once the Volume and domain are configured.
6. Send `/start` to your admin bot.
7. Set the destination:

```text
/set_chat -1001234567890
```

8. Add a wallet:

```text
/add 7xK...abc Whale1
```

The app will create/update the Helius webhook using the Railway HTTPS URL.

## Important: Telegram user account

The Telethon account must be able to send messages to the destination chat. For a channel/group, make sure that account is a member and has permission to post.

The Telegram bot itself does not send the CA.

## Duplicate behavior

CA deduplication is global.

If Wallet A buys CA X first:

```text
CA X
```

is sent once.

If Wallet B buys CA X later, nothing is sent.

The sent CA is stored in SQLite.

Transaction signatures are also stored so Helius retries do not process the same transaction repeatedly.

## Webhook security

Helius sends the configured `Authorization` header. The app checks it against:

```text
Bearer <WEBHOOK_SECRET>
```

Do not publish the secret.

## Health endpoint

`GET /health` returns:

```json
{"ok": true}
```

## Notes

This project does not execute trades. It only observes Solana swaps and forwards the bought mint address.

For newly added wallets, the tracker starts monitoring from that point onward. It does not backfill historical swaps.
