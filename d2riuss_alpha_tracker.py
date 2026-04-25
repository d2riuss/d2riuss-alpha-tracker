import asyncio
import requests
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# --- CONFIGURACIÓN D2RIUSS ALPHA V1.3.2 (SERVER MODE) ---
HELIUS_API_KEY = "ac619ff6-9d50-4a09-99ff-5a03c556302b"
TELEGRAM_BOT_TOKEN = "8648370563:AAEcvkKvDOMUHcYRFb4IGVE5UicnZdWM88"
TELEGRAM_CHAT_ID = "1454858664"

SMART_WALLETS = [
    "4L6YvE6M6KqK9vY7u9cQdJbZ1zV6uH7xN8rG5mP2wE9A",
    "D9uM6pWw9GzR5uJtN6sK9vL2xV4mH3pW6M8K5L9zX7P1",
    "G8nz7KyX6pW9M2vL4sK5uH3pW1zV8M6N7rG5mP9A2eE1",
    "2fR5M9vL4sK6pW8M7rG5uH3pW1zV2xN8rG5mP9A2L6Y7",
    "7ArG5mP9A2eE1zV8M6N7rG5uH3pW4L6YvE6M6KqK9vY7"
]

# --- SERVIDOR WEB PARA ENGAÑAR A RAILWAY ---
class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"D2RIUSS ALPHA IS RUNNING")

def run_server():
    server = HTTPServer(("0.0.0.0", 8080), SimpleServer)
    print("Servidor de red iniciado en puerto 8080")
    server.serve_forever()

# --- LÓGICA DEL BOT ---
def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

async def monitor_wallets():
    print("Iniciando monitorización de carteras élite...")
    send_telegram_msg("🚀 *SISTEMA D2RIUSS V1.3.2 ACTIVO*\n\nEstado: Conectado a red y monitorizando carteras élite.")
    
    processed_txs = set()
    while True:
        try:
            for wallet in SMART_WALLETS:
                url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions?api-key={HELIUS_API_KEY}"
                response = requests.get(url, timeout=12)
                if response.status_code == 200:
                    txs = response.json()
                    for tx in txs:
                        sig = tx.get('signature')
                        if sig and sig not in processed_txs:
                            processed_txs.add(sig)
                            if 'tokenTransfers' in tx and tx['tokenTransfers']:
                                for tr in tx['tokenTransfers']:
                                    if tr.get('toUserAccount') == wallet:
                                        mint = tr.get('mint')
                                        send_telegram_msg(f"💎 *COMPRA ÉLITE*\nWallet: `{wallet[:5]}...` \nToken: `{mint}`\n\n[COMPRAR EN TROJAN](https://t.me/tony_trojanbot?start=r-dariusalpha-{mint})")
            
                await asyncio.sleep(2)
            if len(processed_txs) > 500: processed_txs.clear()
            await asyncio.sleep(20)
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    # Iniciar servidor web en un hilo separado
    threading.Thread(target=run_server, daemon=True).start()
    # Iniciar el bot
    asyncio.run(monitor_wallets())
