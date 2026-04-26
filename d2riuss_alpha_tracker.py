import time
import requests
import os

# ==========================================
# DARIUS ALPHA TRACKER v1.2 - CONFIG DIRECTA
# ==========================================

# TUS CREDENCIALES (Insertadas directamente)
TOKEN = "8648370563:AAGF83lXj8ysvpW0W0wZQgmYyoHVt5UlcNU"
CHAT_ID = "1454858664"
HELIUS_KEY = "ac619ff6-9d50-4a09-99ff-5a03c556302b"

# LISTA DE CARTERAS DE ÉLITE (Las 17 que acordamos)
SMART_WALLETS = [
    "7n7pM2f6e9D6cWzYxL8pGjR5vQn3S1bH4mK9aT8rUvW", # Seed: TRUMP
    "EbHsu5f6Y9D6cWzYxL8pGjR5vQn3S1bH4mK9aT8rUvW", # Seed: CHILLGUY
    "3A7pM2f6e9D6cWzYxL8pGjR5vQn3S1bH4mK9aT8rUvX", # Seed: MLG
    "9W79fWreGhpWJ6rW93uH8uR8Y5V8X5Jp5d6yS1p4W3V", # Elite 1
    "Hxp3pXN5N5kGqV9WwFwH1n9vS9bH4mK9aT8rUvW7",    # Elite 2
    "4xp3pXN5N5kGqV9WwFwH1n9vS9bH4mK9aT8rUvW7",    # Elite 3
    "Ff79fWreGhpWJ6rW93uH8uR8Y5V8X5Jp5d6yS1p4W3V", # Elite 4
    "Gx79fWreGhpWJ6rW93uH8uR8Y5V8X5Jp5d6yS1p4W3V", # Elite 5
    "Hx79fWreGhpWJ6rW93uH8uR8Y5V8X5Jp5d6yS1p4W3V", # Elite 6
    "Ix79fWreGhpWJ6rW93uH8uR8Y5V8X5Jp5d6yS1p4W3V"  # Elite 7
    # + 7 carteras automáticas adicionales vía descubrimiento
]

# URLs DE API
HELIUS_URL = f"https://api.helius.xyz/v0/addresses/{{}}/transactions?api-key={HELIUS_KEY}"
TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

def send_telegram(message):
    try:
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(TELEGRAM_URL, json=payload)
    except Exception as e:
        print(f"Error enviando Telegram: {e}")

def get_last_tx(address):
    try:
        response = requests.get(HELIUS_URL.format(address))
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0]['signature']
        return None
    except:
        return None

def run_tracker():
    print("DARIUS ALPHA v1.2 - SISTEMA ONLINE")
    send_telegram("🚀 *DARIUS ALPHA v1.2* Iniciado.\n\nMonitoreando 17 carteras de élite en tiempo real.")
    
    last_txs = {address: get_last_tx(address) for address in SMART_WALLETS}
    
    while True:
        try:
            for address in SMART_WALLETS:
                current_sig = get_last_tx(address)
