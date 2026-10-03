import aiosqlite
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wallets (
    address TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    added_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS sent_cas (
    mint TEXT PRIMARY KEY,
    first_signature TEXT NOT NULL,
    first_wallet TEXT NOT NULL,
    sent_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS processed_signatures (
    signature TEXT PRIMARY KEY,
    processed_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);
"""

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        await db.commit()

async def get_setting(key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = await cur.fetchone()
        return row[0] if row else None

async def add_wallet(address: str, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO wallets(address,name) VALUES(?,?) "
            "ON CONFLICT(address) DO UPDATE SET name=excluded.name",
            (address, name),
        )
        await db.commit()

async def remove_wallet(address: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM wallets WHERE address=?", (address,))
        await db.commit()
        return cur.rowcount > 0

async def get_wallets():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT address,name FROM wallets ORDER BY added_at ASC")
        return await cur.fetchall()

async def wallet_addresses():
    rows = await get_wallets()
    return [r[0] for r in rows]

async def has_sent_ca(mint: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT 1 FROM sent_cas WHERE mint=?", (mint,))
        return await cur.fetchone() is not None

async def claim_ca(mint: str, signature: str, wallet: str) -> bool:
    """Atomically claim a CA. Returns True only for the first claimant."""
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO sent_cas(mint,first_signature,first_wallet) VALUES(?,?,?)",
                (mint, signature, wallet),
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            await db.rollback()
            return False

async def mark_processed(signature: str) -> bool:
    """Returns True if this signature was new."""
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO processed_signatures(signature) VALUES(?)",
                (signature,),
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            await db.rollback()
            return False
