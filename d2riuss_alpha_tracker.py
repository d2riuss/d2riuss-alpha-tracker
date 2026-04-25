import asyncio
import requests
import json
import os

# --- D2RIUSS ALPHA V1.3.5 (DEBUG MODE) ---
token = "8648370563:AAEcvkKvDOMUHcYRFb4IGVE5UicnZdWM88"
chat_id = "1454858664"
api_key = "ac619ff6-9d50-4a09-99ff-5a03c556302b"

WALLETS = [
    "4L6YvE6M6KqK9vY7u9cQdJbZ1zV6uH7xN8rG5mP2wE9A",
    "D9uM6pWw9GzR5uJtN6sK9vL2xV4mH3pW6M8K5L9zX7P1",
    "G8nz7KyX6pW9M2vL4sK5uH3pW1zV8M6N7rG5mP9A2eE1",
    "2fR5M9vL4sK6pW8M7rG5uH3pW1zV2xN8rG5mP9A2L6Y7",
    "7ArG5mP9A2eE1zV8M6N7rG5uH3pW4L6YvE6M6KqK9vY7"
]

def telegram(msg):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=10)
        print(f"Resultado Telegram: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

async def main():
    print("--- INICIANDO v1.3.5 ---")
    telegram("🚨 *TEST DE CONEXION v1.3.5*\nSi lees esto, el bot ya puede avisarte de las compras.")
    
    vistos = set()
    while True:
        try:
            for w in WALLETS:
                api_url = f"https://api.helius.xyz/v0/addresses/{w}/transactions?api-key={api_key}"
                r = requests.get(api_url, timeout=15)
                if r.status_code == 200:
                    txs = r.json()
                    for tx in txs:
                        s = tx.get('signature')
                        if s and s not in vistos:
                            vistos.add(s)
                            if 'tokenTransfers' in tx:
                                for tr in tx['tokenTransfers']:
                                    if tr.get('toUserAccount') == w:
                                        mint = tr.get('mint')
                                        telegram(f"💎 *COMPRA ÉLITE*\n\nWallet: `{w[:5]}...` \nToken: `{mint}`\n\n[COMPRAR EN TROJAN](https://t.me/tony_trojanbot?start=r-dariusalpha-{mint})")
            
            if len(vistos) > 500: vistos.clear()
            print("Escaneando carteras... Todo OK")
            await asyncio.sleep(40)
        except Exception as e:
            print(f"Error bucle: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
