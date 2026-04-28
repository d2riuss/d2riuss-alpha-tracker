import requests
import time
import os

# CONFIGURACIÓN DIRECTA
API_KEY = "ac619ff6-9d50-4a09-99ff-5a03c556302b"
BOT_TOKEN = "8648370563:AAEcvkKvDOMUHcYRFb4IGVE5UicnZdWM88"
CHAT_ID = "1454858664"

# WALLETS DE ÉLITE
WALLETS = [
    "D88fJqS9Yf9T2o0Yfz7S6sNYKxEnG9nFjGxq",
    "H9nFjGqYf9T2o0Yfz7S6sNYKxEnG9nFjGxq",
    "5W7L5vYf9T2o0Yfz7S6sNYKxEnG9nFjGxq"
]

LAST_TX = {w: None for w in WALLETS}

def alert(txt):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": txt, "parse_mode": "Markdown"})

print(">>> BOT INICIADO - MODO PERSISTENTE <<<", flush=True)

# Bucle infinito
while True:
    try:
        for w in WALLETS:
            # Consultamos la API de Helius
            res = requests.post(
                f"https://mainnet.helius-rpc.com/?api-key={API_KEY}",
                json={"jsonrpc":"2.0","id":1,"method":"getSignaturesForAddress","params":[w,{"limit":1}]},
                timeout=10
            ).json()
            
            curr = res.get("result", [{}])[0].get("signature")
            
            if curr:
                if LAST_TX[w] is None:
                    LAST_TX[w] = curr
                    print(f"Sincronizada: {w[:5]}", flush=True)
                elif curr != LAST_TX[w]:
                    LAST_TX[w] = curr
                    alert(f"🔥 **GEMA:**\nWallet: `{w}`\n[Solscan](https://solscan.io/tx/{curr})")
                    print(f"ALERTA ENVIADA", flush=True)
            
            time.sleep(5) # Pausa para no saturar
            
        print("--- Bot activo y esperando ---", flush=True)
        
    except Exception as e:
        print(f"Reintentando por error: {e}", flush=True)
        time.sleep(10)
