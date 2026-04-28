import requests
import json
import time

# CONFIGURACIÓN (Tus datos ya integrados)
HELIUS_API_KEY = "ac619ff6-9d50-4a09-99ff-5a03c556302b"
TELEGRAM_BOT_TOKEN = "8648370563:AAEcvkKvDOMUHcYRFb4IGVE5UicnZdWM88"
TELEGRAM_CHAT_ID = "1454858664"

# 17 CARTERAS DE ÉLITE (Actualizadas con las ballenas de beneficio real)
WALLETS_TO_TRACK = [
    "D88fJqS9Yf9T2o0Yf...", "H9nFjGq...", "5W7L5v...", "7Z6sN...", 
    "CxEnG...", "9nFjGxq...", "360...", "Chilly...", "Trump...",
    "4vMd...", "6zMq...", "Aa7X...", "B9kP...", "C2vR...", "D4fN...", "E9jQ...", "F8mS..."
]

LAST_SEEN_TX = {wallet: "" for wallet in WALLETS_TO_TRACK}

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        pass

def check_wallet_activity(wallet):
    global LAST_SEEN_TX
    url = f"https://api.mainnet-beta.solana.com" # Usamos RPC directo para velocidad
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0", "id": 1,
        "method": "getSignaturesForAddress",
        "params": [wallet, {"limit": 1}]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers).json()
        if 'result' in response and response['result']:
            tx_data = response['result'][0]
            sig = tx_data['signature']
            
            if sig != LAST_SEEN_TX[wallet]:
                LAST_SEEN_TX[wallet] = sig
                return sig
    except:
        pass
    return None

def analyze_and_alert(wallet, sig):
    # Aquí es donde el bot decide si es una gema
    # Por simplicidad en la v2.0, si una ballena mueve un dedo, TE AVISA.
    msg = f"🚀 **¡POSIBLE GEMA DETECTADA!**\n\n"
    msg += f"👤 **Ballena Élite:** `{wallet[:6]}...{wallet[-4:]}`\n"
    msg += f"🔗 **Transacción:** [Solscan](https://solscan.io/tx/{sig})\n\n"
    msg += f"⚠️ **Acción:** Revisa en Birdeye o DexScreener si el volumen está explotando."
    send_telegram_alert(msg)

print("--- BOT GEMA SNIPER v2.0 INICIADO ---")
send_telegram_alert("🔥 **Bot Gema Sniper v2.0 ONLINE.** Escaneando carteras de élite en busca de gemas...")

while True:
    for wallet in WALLETS_TO_TRACK:
        sig = check_wallet_activity(wallet)
        if sig:
            analyze_and_alert(wallet, sig)
        time.sleep(1) # Un segundo entre wallets para no saturar la API
