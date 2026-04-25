import asyncio
import requests
import json
import time

# --- CONFIGURACIÓN D2RIUSS ALPHA V1.3.1 (STABLE) ---
HELIUS_API_KEY = "ac619ff6-9d50-4a09-99ff-5a03c556302b"
TELEGRAM_BOT_TOKEN = "8648370563:AAEcvkKvDOMUHcYRFb4IGVE5UicnZdWM88"
TELEGRAM_CHAT_ID = "1454858664"

# LAS 5 WALLETS ÉLITE 
SMART_WALLETS = [
    "4L6YvE6M6KqK9vY7u9cQdJbZ1zV6uH7xN8rG5mP2wE9A",
    "D9uM6pWw9GzR5uJtN6sK9vL2xV4mH3pW6M8K5L9zX7P1",
    "G8nz7KyX6pW9M2vL4sK5uH3pW1zV8M6N7rG5mP9A2eE1",
    "2fR5M9vL4sK6pW8M7rG5uH3pW1zV2xN8rG5mP9A2L6Y7",
    "7ArG5mP9A2eE1zV8M6N7rG5uH3pW4L6YvE6M6KqK9vY7"
]

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error Telegram: {e}")

async def monitor_wallets():
    print("--- D2RIUSS ALPHA TRACKER v1.3.1 ONLINE ---")
    print("Estado: Manteniendo contenedor vivo...")
    
    send_telegram_msg("🚀 *DARIUS ALPHA V1.3.1 ACTIVADO*\n\nMonitorizando las 5 carteras élite. Sistema estable.")

    processed_txs = set()

    while True:
        try:
            for wallet in SMART_WALLETS:
                url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions?api-key={HELIUS_API_KEY}"
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    txs = response.json()
                    for tx in txs:
                        signature = tx.get('signature')
                        if signature and signature not in processed_txs:
                            processed_txs.add(signature)
                            
                            if 'tokenTransfers' in tx and tx['tokenTransfers']:
                                for transfer in tx['tokenTransfers']:
                                    if transfer.get('toUserAccount') == wallet:
                                        token_address = transfer.get('mint')
                                        
                                        msg = (
                                            f"💎 *NUEVA COMPRA ÉLITE*\n\n"
                                            f"👤 *Wallet:* `{wallet[:6]}...{wallet[-4:]}`\n"
                                            f"📄 *Token:* `{token_address}`\n\n"
                                            f"🔥 *COMPRAR EN TROJAN:*\n"
                                            f"https://t.me/tony_trojanbot?start=r-dariusalpha-{token_address}"
                                        )
                                        send_telegram_msg(msg)
                                        print(f"Alerta: {token_address}")
            
                # Limpiar memoria para que Railway no se sature
                if len(processed_txs) > 1000:
                    processed_txs.clear()
                    
                await asyncio.sleep(5) # Espera pequeña entre cada chequeo de wallet
                
            await asyncio.sleep(20) # Pausa larga para evitar bloqueo de Railway/Helius
            
        except Exception as e:
            print(f"Error detectado: {e}. Reintentando en 30s...")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(monitor_wallets())
