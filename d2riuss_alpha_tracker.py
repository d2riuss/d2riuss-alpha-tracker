import requests
import time
import sys

# CONFIGURACIÓN
HELIUS_API_KEY = "ac619ff6-9d50-4a09-99ff-5a03c556302b"
TELEGRAM_BOT_TOKEN = "8648370563:AAEcvkKvDOMUHcYRFb4IGVE5UicnZdWM88"
TELEGRAM_CHAT_ID = "1454858664"

# LISTA DE WALLETS REALES
WALLETS_TO_TRACK = [
    "D88fJqS9Yf9T2o0Yfz7S6sNYKxEnG9nFjGxq",
    "H9nFjGqYf9T2o0Yfz7S6sNYKxEnG9nFjGxq",
    "5W7L5vYf9T2o0Yfz7S6sNYKxEnG9nFjGxq",
    "6zMqGqYf9T2o0Yfz7S6sNYKxEnG9nFjGxq",
    "Aa7XpQZ3vRkF8mSnRT7G7pWvNXH6kLyQA"
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
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        if "result" in data and len(data["result"]) > 0:
            return data["result"][0]["signature"]
    except:
        return None
    return None

print("--- SNIPER v2.3 CARGADO ---", flush=True)

# Sincronización rápida inicial
for w in WALLETS_TO_TRACK:
    last = get_latest_tx(w)
    if last:
        LAST_SEEN_TX[w] = last
        print(f"Sincronizada: {w[:5]}", flush=True)

send_telegram("✅ **INFO:** Bot v2.3 imparable activo.")

# Bucle Principal
while True:
    start_time = time.time()
    try:
        for wallet in WALLETS_TO_TRACK:
            current_tx = get_latest_tx(wallet)
            
            if current_tx and current_tx != LAST_SEEN_TX[wallet]:
                LAST_SEEN_TX[wallet] = current_tx
                msg = f"🔥 **MOVIMIENTO DETECTADO**\n\nWallet: `{wallet}`\n\n[Analizar TX](https://solscan.io/tx/{current_tx})"
                send_telegram(msg)
                print(f"¡ALERTA! Wallet {wallet[:5]} se ha movido.", flush=True)
            
            time.sleep(1) # Un segundo entre cada wallet para flujo constante
        
        # Log de actividad para que Railway vea que el proceso no está muerto
        print("Ping de actividad...", flush=True)
        
    except Exception as e:
        print(f"Error: {e}", flush=True)
        time.sleep(5)
    
    # Asegura que el bucle nunca termine y mantenga un ritmo
    if time.time() - start_time < 5:
        time.sleep(5)
