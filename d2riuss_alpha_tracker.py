import requests
import time

HELIUS_API_KEY = "ac619ff6-9d50-4a09-99ff-5a03c556302b"
TELEGRAM_BOT_TOKEN = "8648370563:AAEcvkKvDOMUHcYRFb4IGVE5UicnZdWM88"
TELEGRAM_CHAT_ID = "1454858664"

WALLETS_TO_TRACK = [
    "D88fJqS9Yf9T2o0Yfz7S6sNYKxEnG9nFjGxq",
    "H9nFjGqYf9T2o0Yfz7S6sNYKxEnG9nFjGxq",
    "5W7L5vYf9T2o0Yfz7S6sNYKxEnG9nFjGxq"
]

LAST_SEEN_TX = {wallet: None for wallet in WALLETS_TO_TRACK}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

def get_latest_tx(wallet):
    url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [wallet, {"limit": 1}]
    }
    try:
        response = requests.post(url, json=payload, timeout=15).json()
        if "result" in response and len(response["result"]) > 0:
            return response["result"][0]["signature"]
    except:
        pass
    return None

print("--- SNIPER v2.1 INICIADO ---")
send_telegram("🚀 **INFO:** Bot Online. Escaneando carteras élite...")

while True:
    try:
        for wallet in WALLETS_TO_TRACK:
            current_tx = get_latest_tx(wallet)
            if current_tx:
                if LAST_SEEN_TX[wallet] is None:
                    LAST_SEEN_TX[wallet] = current_tx
                    print(f"Sincronizada: {wallet[:5]}")
                elif current_tx != LAST_SEEN_TX[wallet]:
                    LAST_SEEN_TX[wallet] = current_tx
                    msg = "💎 **ALERTA DE GEMA**\n\n"
                    msg += f"👤 **Wallet:** `{wallet}`\n"
                    msg += f"🔗 **TX:** [Solscan](https://solscan.io/tx/{current_tx})"
                    send_telegram(msg)
                    print(f"¡Alerta enviada!")
            time.sleep(2)
    except:
        time.sleep(10)
