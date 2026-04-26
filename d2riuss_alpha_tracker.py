import time
import requests
import sys

# CONFIGURACIÓN
TOKEN = "8648370563:AAGF83lXj8ysvpW0W0wZQgmYyoHVt5UlcNU"
CHAT_ID = "1454858664"
HELIUS_KEY = "ac619ff6-9d50-4a09-99ff-5a03c556302b"

WALLETS = [
    "7n7pM2f6e9D6cWzYxL8pGjR5vQn3S1bH4mK9aT8rUvW",
    "EbHsu5f6Y9D6cWzYxL8pGjR5vQn3S1bH4mK9aT8rUvW",
    "3A7pM2f6e9D6cWzYxL8pGjR5vQn3S1bH4mK9aT8rUvX"
]

def enviar(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except: pass

if __name__ == "__main__":
    print("SISTEMA DARIUS ONLINE", flush=True)
    enviar("🔋 BOT REINICIADO - VIGILANCIA FIJA")
    
    sigs = {}
    while True:
        for w in WALLETS:
            try:
                r = requests.get(f"https://api.helius.xyz/v0/addresses/{w}/transactions?api-key={HELIUS_KEY}", timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    if data:
                        s = data[0]['signature']
                        if w in sigs and s != sigs[w]:
                            enviar(f"🔥 MOVIMIENTO: {w[:5]}\nhttps://solscan.io/tx/{s}")
                        sigs[w] = s
            except: pass
            time.sleep(5)
        # Esto imprime en el log para que Railway vea actividad constante
        print("Ping de actividad...", flush=True)
        time.sleep(10)
