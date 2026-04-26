import time
import requests
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# ==========================================
# DARIUS ALPHA TRACKER v1.3 - ULTRA STABLE
# ==========================================

TOKEN = "8648370563:AAGF83lXj8ysvpW0W0wZQgmYyoHVt5UlcNU"
CHAT_ID = "1454858664"
HELIUS_KEY = "ac619ff6-9d50-4a09-99ff-5a03c556302b"

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

HELIUS_URL = f"https://api.helius.xyz/v0/addresses/{{}}/transactions?api-key={HELIUS_KEY}"
TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# Mini servidor para que Railway no apague el contenedor
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

def send_telegram(message):
    try:
        requests.post(TELEGRAM_URL, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

def get_last_tx(address):
    try:
        response = requests.get(HELIUS_URL.format(address), timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data[0]['signature'] if data else None
    except:
        return None
    return None

def run_tracker():
    print("DARIUS ALPHA v1.3 - SISTEMA ONLINE")
    send_telegram("🚀 *DARIUS ALPHA v1.3* - Estabilidad mejorada.\nBot vigilando.")
    
    last_txs = {}
    # No precargamos para evitar errores de inicio, el bot aprende las firmas en la primera vuelta
    
    while True:
        for address in SMART_WALLETS:
            try:
                current_sig = get_last_tx(address)
                if current_sig:
                    if address in last_txs and current_sig != last_txs[address]:
                        msg = f"🔥 *MOVIMIENTO DETECTADO*\n\nCartera: `{address[:6]}...{address[-4:]}`\nTX: `https://solscan.io/tx/{current_sig}`"
                        send_telegram(msg)
                    last_txs[address] = current_sig
                time.sleep(3) # Pausa más larga entre carteras para evitar límites de API
            except:
                time.sleep(10)
        time.sleep(5)

if __name__ == "__main__":
    # Arrancamos el servidor de salud en un hilo aparte
    threading.Thread(target=run_health_server, daemon=True).start()
    # Arrancamos el tracker
    run_tracker()
