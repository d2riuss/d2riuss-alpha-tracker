import requests
import time
import sys

# CONFIGURACIÓN
HELIUS_API_KEY = "ac619ff6-9d50-4a09-99ff-5a03c556302b"
TELEGRAM_BOT_TOKEN = "8648370563:AAEcvkKvDOMUHcYRFb4IGVE5UicnZdWM88"
TELEGRAM_CHAT_ID = "1454858664"

# 17 CARTERAS DE ÉLITE FILTRADAS
WALLETS_TO_TRACK = [
    "D88fJqS9Yf9T2o0Yfz7S6sNYKxEnG9nFjGxq", "H9nFjGqYf9T2o0Yfz7S6sNYKxEnG9nFjGxq",
    "5W7L5vYf9T2o0Yfz7S6sNYKxEnG9nFjGxq", "Aa7XpQZ...", "B9kPrSY...", 
    "C2vRfGX...", "D4fNkLA...", "E9jQmZS...", "F8mSnRT...", "G7pWvNX...",
    "H6kLyQA...", "J5rTzBM...", "K4vNcDL...", "L3mXpQS...", "M2kRyFA...",
    "N1pWvNZ...", "P9jQmZT..." # Añade aquí las direcciones completas que tienes
]

# Diccionario para controlar la última transacción vista
LAST_SEEN_TX = {wallet: None for wallet in WALLETS_TO_TRACK}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")
        return False

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
    except Exception as e:
        print(f"Error consultando wallet {wallet[:5]}: {e}")
    return None

print("--- SNIPER v2.1 INICIADO (MODO TANQUE) ---")
send_telegram("🚀 **INFO:** Bot v2.1 Online. Vigilando gemas de ballenas...")

while True:
    try:
        for wallet in WALLETS_TO_TRACK:
            current_tx = get_latest_tx(wallet)
            
            if current_tx:
                # Sincronización inicial: la primera vez que detecta la wallet,
