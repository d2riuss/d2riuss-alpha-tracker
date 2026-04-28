import requests
import time

HELIUS_API_KEY = "ac619ff6-9d50-4a09-99ff-5a03c556302b"
BOT_TOKEN = "8648370563:AAEcvkKvDOMUHcYRFb4IGVE5UicnZdWM88"
CHAT_ID = "1454858664"

# Asegúrate de que estas direcciones son 100% correctas
WALLETS = [
    "D88fJqS9Yf9T2o0Yfz7S6sNYKxEnG9nFjGxq",
    "H9nFjGqYf9T2o0Yfz7S6sNYKxEnG9nFjGxq",
    "5W7L5vYf9T2o0Yfz7S6sNYKxEnG9nFjGxq",
    "Aa7XpQZ3vRkF8mSnRT7G7pWvNXH6kLyQA" # Añade todas las que quieras aquí
]

LAST_TX = {w: None for w in WALLETS}

def alert(txt):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": txt, "parse_mode": "Markdown"}, timeout=5)
    except: pass

print(">>> SISTEMA GEMA-HUNTER v2.4 <<<", flush=True)

# Test de Telegram inmediato tras reiniciar
alert("⚡️ **SISTEMA REINICIADO:** Modo Agresivo (v2.4) activado. Escaneando cada 0.5s.")

while True:
    try:
        for w in WALLETS:
            res = requests.post(
                f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}",
                json={"jsonrpc":"2.0","id":1,"method":"getSignaturesForAddress","params":[w,{"limit":1}]},
                timeout=10
            ).json()
            
            curr = res.get("result", [{}])[0].get("signature")
            
            if curr:
                # Sincronización
                if LAST_TX[w] is None:
                    LAST_TX[w] = curr
                    print(f"Sync: {w[:5]}", flush=True)
                # ¡NUEVA ALERTA!
                elif curr != LAST_TX[w]:
                    LAST_TX[w] = curr
                    alert(f"🔥 **MOVIMIENTO DETECTADO**\nWallet: `{w}`\n[Ver TX](https://solscan.io/tx/{curr})")
                    print(f"!!! ALERTA {w[:5]} !!!", flush=True)
            
            time.sleep(0.5) # Velocidad máxima: solo medio segundo entre wallets
            
    except Exception as e:
        print(f"Error: {e}", flush=True)
        time.sleep(5)
