from config import QUOTE_MINTS

def _account(obj):
    return obj.get("userAccount") or obj.get("account")

def _mint(obj):
    return obj.get("mint")

def _contains_native_input_for_wallet(swap: dict, wallet: str) -> bool:
    native = swap.get("nativeInput") or {}
    return native.get("account") == wallet and int(native.get("amount") or 0) > 0

def _wallet_quote_token_input(swap: dict, wallet: str) -> bool:
    for item in swap.get("tokenInputs") or []:
        if _account(item) == wallet and _mint(item) in QUOTE_MINTS:
            amount = item.get("rawTokenAmount", {}).get("tokenAmount")
            if amount is not None and int(amount) > 0:
                return True
    return False

def extract_bought_mints(payload: dict, watched_wallets: set[str]) -> list[tuple[str, str]]:
    """
    Returns (wallet, mint) pairs that look like actual buys.

    We require:
      - Helius says SWAP
      - wallet receives the output token
      - output is not a quote mint
      - wallet pays native SOL OR a configured quote SPL token
    """
    if payload.get("type") != "SWAP":
        return []

    events = payload.get("events") or {}
    swap = events.get("swap") or {}
    if not swap:
        return []

    outputs = swap.get("tokenOutputs") or []
    results = []

    for wallet in watched_wallets:
        paid = (
            _contains_native_input_for_wallet(swap, wallet)
            or _wallet_quote_token_input(swap, wallet)
        )
        if not paid:
            continue

        for out in outputs:
            if _account(out) != wallet:
                continue
            mint = _mint(out)
            if not mint or mint in QUOTE_MINTS:
                continue
            raw = (out.get("rawTokenAmount") or {}).get("tokenAmount")
            if raw is not None:
                try:
                    if int(raw) <= 0:
                        continue
                except (TypeError, ValueError):
                    pass
            results.append((wallet, mint))

    # Stable order and no duplicates within one transaction.
    return list(dict.fromkeys(results))
