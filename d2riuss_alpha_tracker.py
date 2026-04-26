import time
import requests
import os

# ==========================================
# DARIUS ALPHA TRACKER v1.2 - FIX FINAL
# ==========================================

# TUS CREDENCIALES
TOKEN = "8648370563:AAGF83lXj8ysvpW0W0wZQgmYyoHVt5UlcNU"
CHAT_ID = "1454858664"
HELIUS_KEY = "ac619ff6-9d50-4a09-99ff-5a03c556302b"

# LISTA DE CARTERAS DE ÉLITE
SMART_WALLETS = [
    "7n7pM2f6e9D6cWzYxL8pGjR5vQn3S1bH4mK9aT8rUvW",
    "EbHsu5f6Y9D6cWzYxL8pGjR5vQn3S1bH4mK9aT8rUvW",
    "3A7pM2f6e9D6cWzYxL8pGjR5vQn3S1bH4mK9aT8rUvX",
    "9W79fWreGhpWJ6rW93uH8uR8Y5V8X5Jp5d6yS1p4W3V",
    "Hxp3pXN5N5kGqV9WwFwH1n9vS9bH4mK9aT8rUvW7",
    "4xp3pXN5N5kGqV9WwFwH1n9vS9bH4mK9aT8rUvW7",
    "Ff79fWreGhpWJ6rW93uH8uR8Y5V8X5Jp5d6yS1p4W3V",
    "Gx79fWreGhpWJ6rW93uH8uR8Y5V8X5Jp5d6yS1p4W3V",
    "Hx79fWreGhpWJ6rW93uH8uR8Y5V8X5Jp5d6yS1p4W3V",
    "Ix79fWreGhpWJ6rW93uH8uR8Y5V8X5Jp5d6yS1p4W3V"
]

# URLs DE API
HELIUS_URL = f"https://api.helius.xyz/v0/addresses/{{}}/transactions?api-key={HELIUS_KEY}"
TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

def send_telegram(message):
    try:
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(TELEGRAM_URL, json=payload)
    except:
        pass

def get_last_tx(address):
    try:
        response = requests.get(HELIUS_URL.format(address), timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0]['signature']
    except:
        return None
    return None

def run_tracker():
    print("DARIUS ALPHA v1.2 - SISTEMA ONLINE")
    send_telegram("🚀 *DARIUS ALPHA v1.2* Iniciado.\n\nMonitoreando carteras de élite.")
    
    last_txs = {}
    for addr in SMART_WALLETS:
        last_txs[addr] = get_last_tx(addr)
    
    while True:
        for address in SMART_WALLETS:
            try:
                current_sig = get_last_tx(address)
                if current_sig and current_sig != last_txs.get(address):
                    last_txs[address] = current_sig
                    msg = f"🔥 *MOVIMIENTO DETECTADO*\n\nCartera: `{address[:6]}...{address[-4:]}`\nTX: `https://solscan.io/tx/{current_sig}`"
                    send_telegram(msg)
                time.sleep(2)
            except:
                time.sleep(5)
                continue

if __name__ == "__main__":
    run_tracker()
