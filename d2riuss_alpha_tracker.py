import time
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import os

# ==========================================
# DARIUS ALPHA - VERSIÓN ANTI-CIERRE
# ==========================================

TOKEN = "8648370563:AAGF83lXj8ysvpW0W0wZQgmYyoHVt5UlcNU"
CHAT_ID = "1454858664"
HELIUS_KEY = "ac619ff6-9d50-4a09-99ff-5a03c556302b"

WALLETS = [
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

# Servidor web falso para que Railway no lo apague
class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Darius Alpha is Running")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), WebServer)
    server.serve_forever()

def enviar(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    except: pass

def check_loop():
    print("SISTEMA DARIUS ONLINE - VIGILANDO CARTERAS")
    enviar("🔥 DARIUS ALPHA ACTIVO - Modo Anti-Cierre")
    ultimas_sigs = {}
    while True:
        for w in WALLETS:
            try:
                url_h = f"https://api.helius.xyz/v0/addresses/{w}/transactions?api-key={HELIUS_KEY}"
                r = requests.get(url_h, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    if data:
                        sig = data[0]['signature']
                        if w in ultimas_sigs and sig != ultimas_sigs[w]:
                            enviar(f"⚠️ MOVIMIENTO: {w[:5]}...\nhttps://solscan.io/tx/{sig}")
                        ultimas_sigs[w] = sig
                time.sleep(2)
            except: time.sleep(5)

if __name__ == "__main__":
    # Inicia servidor web en segundo plano
    threading.Thread(target=run_web_server, daemon=True).start()
    # Inicia el bot
    check_loop()
