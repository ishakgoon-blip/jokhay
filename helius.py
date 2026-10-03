import aiohttp
from config import HELIUS_API_KEY, WEBHOOK_SECRET, webhook_url

API = "https://api.helius.xyz/v0/webhooks"

class HeliusError(RuntimeError):
    pass

async def _request(method: str, url: str, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, timeout=aiohttp.ClientTimeout(total=30), **kwargs) as r:
            text = await r.text()
            if r.status >= 400:
                raise HeliusError(f"Helius HTTP {r.status}: {text[:1000]}")
            try:
                return await r.json()
            except Exception:
                return text

async def get_webhooks():
    return await _request("GET", f"{API}?api-key={HELIUS_API_KEY}")

async def create_webhook(addresses: list[str], base_url: str | None = None):
    if not addresses:
        return None
    payload = {
        "webhookURL": webhook_url(base_url),
        "transactionTypes": ["SWAP"],
        "accountAddresses": addresses,
        "webhookType": "enhanced",
        "authHeader": f"Bearer {WEBHOOK_SECRET}",
    }
    return await _request(
        "POST",
        f"{API}?api-key={HELIUS_API_KEY}",
        json=payload,
        headers={"Content-Type": "application/json"},
    )

async def update_webhook(webhook_id: str, addresses: list[str], base_url: str | None = None):
    if not addresses:
        return await delete_webhook(webhook_id)
    payload = {
        "webhookURL": webhook_url(base_url),
        "transactionTypes": ["SWAP"],
        "accountAddresses": addresses,
        "webhookType": "enhanced",
        "authHeader": f"Bearer {WEBHOOK_SECRET}",
    }
    return await _request(
        "PUT",
        f"{API}/{webhook_id}?api-key={HELIUS_API_KEY}",
        json=payload,
        headers={"Content-Type": "application/json"},
    )

async def delete_webhook(webhook_id: str):
    return await _request(
        "DELETE",
        f"{API}/{webhook_id}?api-key={HELIUS_API_KEY}"
    )

async def reconcile_webhook(addresses: list[str], base_url: str | None = None):
    """
    Finds our webhook by exact URL + SWAP/enhanced shape and reconciles it.
    If none exists, creates one.
    """
    hooks = await get_webhooks()
    target_url = webhook_url(base_url)

    ours = None
    for h in hooks if isinstance(hooks, list) else []:
        if h.get("webhookURL") == target_url and h.get("webhookType") == "enhanced":
            ours = h
            break

    if not addresses:
        if ours:
            await delete_webhook(ours["webhookID"])
        return None

    if ours:
        await update_webhook(ours["webhookID"], addresses, base_url)
        return ours["webhookID"]

    created = await create_webhook(addresses, base_url)
    return created.get("webhookID")
