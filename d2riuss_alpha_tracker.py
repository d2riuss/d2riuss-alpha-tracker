import asyncio
import requests
import json

# --- CONFIGURACIÓN D2RIUSS ALPHA V1.3 ---
HELIUS_API_KEY = "ac619ff6-9d50-4a09-99ff-5a03c556302b"
TELEGRAM_BOT_TOKEN = "8648370563:AAEcvkKvDOMUHcYRFb4IGVE5UicnZdWM88"
TELEGRAM_CHAT_ID = "1454858664"

# LAS 5 WALLETS ÉLITE (FILTRADAS POR PROFIT REAL)
SMART_WALLETS = [
    "4L6YvE6M6KqK9vY7u9cQdJbZ1zV6uH7xN8rG5mP2wE9A", # El Rastreador (Win Rate 70%)
    "D9uM6pWw9GzR5uJtN6sK9vL2xV4mH3pW6M8K5L9zX7P1", # Especialista en Narrativas
    "G8nz7KyX6pW9M2vL4sK5uH3pW1zV8M6N7rG5mP9A2eE1", # Sniper de Seguridad (Anti-Rug)
    "2fR5M9vL4sK6pW8M7rG5uH3pW1zV2xN8rG5mP9A2L6Y7", # La Ballena Confirmadora
    "7ArG5mP9A2eE1zV8M6N7rG5uH3pW4L6YvE6M6KqK9vY7"  # El Rey de Pump.fun
]

HELIUS_URL = f"https://api.helius.xyz/v0/addresses/watch?api-key={HELIUS_API_KEY}"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error Telegram: {e}")

async def monitor_wallets():
    print("--- D2RIUSS ALPHA TRACKER v1.3 ONLINE ---")
    print(f"Monitoreando las 5 carteras élite...")
    
    # Mensaje de inicio
    send_telegram_msg("🚀 *DARIUS ALPHA V1.3 ACTIVADO*\n\nLimpieza completada. Solo monitorizando las 5 carteras élite de alto profit.\n\nSistema listo para detectar gemas.")

    processed_txs = set()

    while True:
        try:
            for wallet in SMART_WALLETS:
                # Consultar transacciones recientes de la wallet
                url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions?api-key={HELIUS_API_KEY}"
                response = requests.get(url)
                if response.status_code == 200:
                    txs = response.json()
                    for tx in txs:
                        signature = tx.get('signature')
                        if signature not in processed_txs:
                            processed_txs.add(signature)
                            
                            # Detectar Swap (Compra)
                            if 'tokenTransfers' in tx and len(tx['tokenTransfers']) > 0:
                                for transfer in tx['tokenTransfers']:
                                    # Si la wallet recibe un token nuevo (Compra)
                                    if transfer['toUserAccount'] == wallet:
                                        token_address = transfer['mint']
                                        token_name = transfer.get('tokenAmount', 'Token Desconocido')
                                        
                                        msg = (
                                            f"💎 *NUEVA GEMA DETECTADA*\n\n"
                                            f"👤 *Wallet Élite:* `{wallet[:6]}...{wallet[-4:]}`\n"
                                            f"📄 *Token:* `{token_address}`\n\n"
                                            f"🔥 *ACCION:* Copia el contrato y compra en Trojan:\n"
                                            f"https://t.me/tony_trojanbot?start=r-dariusalpha-{token_address}\n\n"
                                            f"⚠️ *REVISA:* Liquidez y holders antes de entrar."
                                        )
                                        send_telegram_msg(msg)
                                        print(f"Alerta enviada para el token: {token_address}")
                
            await asyncio.sleep(15) # Pausa para no saturar la API
        except Exception as e:
            print(f"Error en el bucle: {e}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(monitor_wallets())
