import asyncio
import requests

# --- DARIUS ALPHA v1.3.7 ---
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

def telegram_msg(texto):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    datos = {"chat_id": chat_id, "text": texto, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        r = requests.post(url, json=datos, timeout=10)
        print(f"Enviado a Telegram: {r.status_code}")
    except Exception as e:
        print(f"Error Telegram: {e}")

async def main():
    print("--- DARIUS ALPHA v1.3.7 ONLINE ---")
    telegram_msg("🚀 *DARIUS ALPHA v1.3.7 CONECTADO*\n\nVigilando las 5 carteras élite.")
    
    vistos = set()
    while True:
        try:
            for w in WALLETS:
                url_helius = f"https://api.helius.xyz/v0/addresses/{w}/transactions?api-key={api_key}"
                res = requests.get(url_helius, timeout=15)
                if res.status_code == 200:
                    for tx in res.json():
                        sig = tx.get('signature')
                        if sig and sig not in vistos:
                            vistos.add(sig)
                            if 'tokenTransfers' in tx:
                                for tr in tx['tokenTransfers']:
                                    if tr.get('toUserAccount') == w:
                                        mint = tr.get('mint')
                                        telegram_msg(f"💎 *COMPRA ÉLITE*\nWallet: `{w[:5]}...` \nToken: `{mint}`\n\n[COMPRAR EN TROJAN](https://t.me/tony_trojanbot?start=r-dariusalpha-{mint})")
            
            if len(vistos) > 500: vistos.clear()
            print("Escaneando carteras... OK")
            await asyncio.sleep(40)
        except Exception as e:
            print(f"Fallo bucle: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
