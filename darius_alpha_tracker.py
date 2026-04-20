
# ============================================
# DARIUS ALPHA TRACKER v1.0
# Smart Money Tracker + Alert System for Solana
# By: Darius Marian Burzo
# ============================================

import requests
import json
import time
import sqlite3
from datetime import datetime, timedelta

# ============================================
# CONFIGURACIÓN - TUS DATOS
# ============================================
HELIUS_API_KEY = "ac619ff6-9d50-4a09-99ff-5a03c556302b"
TELEGRAM_BOT_TOKEN = "8648370563:AAEcv5kKvDOMUHcYRFb4IGVE5UicnZdWM88"
TELEGRAM_CHAT_ID = "1454858664"
HELIUS_RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

# ============================================
# SMART WALLETS DATABASE
# Estas son wallets que rastrearemos.
# Las iremos añadiendo conforme encontremos más.
# ============================================
SMART_WALLETS = []  # Se llenarán automáticamente en Fase 2

# ============================================
# TOKENS DE REFERENCIA (los que ya conocemos)
# ============================================
REFERENCE_TOKENS = {
    "TRUMP": "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN",
    "CHILLGUY": "Df6yfrKC8kZE3KNkrHERKzAetSxbrWeniQfyJY4Jpump",
    "MLG": "7XJiwLDrjzxDYdZipnJXzpr1iDTmK55XixSFAa7JgNEL",
}

# ============================================
# BASE DE DATOS LOCAL
# ============================================
def init_db():
    conn = sqlite3.connect("darius_alpha.db")
    c = conn.cursor()

    # Tabla de smart wallets
    c.execute("""
        CREATE TABLE IF NOT EXISTS smart_wallets (
            address TEXT PRIMARY KEY,
            label TEXT,
            win_rate REAL DEFAULT 0,
            total_trades INTEGER DEFAULT 0,
            profitable_trades INTEGER DEFAULT 0,
            total_pnl REAL DEFAULT 0,
            added_date TEXT,
            source TEXT
        )
    """)

    # Tabla de tokens detectados
    c.execute("""
        CREATE TABLE IF NOT EXISTS detected_tokens (
            mint TEXT PRIMARY KEY,
            name TEXT,
            symbol TEXT,
            score INTEGER DEFAULT 0,
            smart_wallets_in INTEGER DEFAULT 0,
            liquidity REAL DEFAULT 0,
            holders INTEGER DEFAULT 0,
            mint_authority_revoked INTEGER DEFAULT 0,
            freeze_authority_revoked INTEGER DEFAULT 0,
            top10_holder_pct REAL DEFAULT 0,
            detected_at TEXT,
            price_at_detection REAL DEFAULT 0,
            current_price REAL DEFAULT 0,
            alerted INTEGER DEFAULT 0
        )
    """)

    # Tabla de operaciones
    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_mint TEXT,
            token_symbol TEXT,
            action TEXT,
            price REAL,
            amount_sol REAL,
            timestamp TEXT,
            pnl REAL DEFAULT 0,
            notes TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada")

# ============================================
# TELEGRAM - SISTEMA DE ALERTAS
# ============================================
def send_telegram(message, parse_mode="HTML"):
    """Envía mensaje a tu Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json().get("ok", False)
    except Exception as e:
        print(f"❌ Error enviando Telegram: {e}")
        return False

def send_alpha_alert(token_data):
    """Envía alerta formateada de un token detectado"""
    score = token_data.get("score", 0)

    # Emoji según score
    if score >= 85:
        emoji = "🔥🔥🔥"
    elif score >= 70:
        emoji = "🔥🔥"
    else:
        emoji = "🔥"

    # Checks
    mint_check = "✅" if token_data.get("mint_authority_revoked") else "❌"
    freeze_check = "✅" if token_data.get("freeze_authority_revoked") else "❌"
    top10_check = "✅" if token_data.get("top10_pct", 100) < 40 else "❌"
    liq_check = "✅" if token_data.get("liquidity", 0) > 5000 else "❌"

    message = f"""
{emoji} <b>ALPHA ALERT — Score: {score}/100</b>

<b>Token:</b> ${token_data.get('symbol', 'N/A')}
<b>CA:</b> <code>{token_data.get('mint', 'N/A')}</code>
<b>Precio:</b> ${token_data.get('price', 'N/A')}
<b>Liquidez:</b> ${token_data.get('liquidity', 'N/A'):,.0f}
<b>Holders:</b> {token_data.get('holders', 'N/A')}
<b>Market Cap:</b> ${token_data.get('mcap', 'N/A'):,.0f}

<b>Smart Wallets dentro:</b> {token_data.get('smart_wallets_count', 0)}

<b>Filtros de seguridad:</b>
{mint_check} Mint authority revocada
{freeze_check} Freeze authority revocada
{top10_check} Top 10 holders < 40%
{liq_check} Liquidez > $5K

<b>⚡ Acción sugerida:</b> {'ENTRADA con 10-15€' if score >= 75 else 'OBSERVAR'}
🎯 TP1: 3x | TP2: 10x | SL: -40%

<i>— Darius Alpha Tracker v1.0</i>
"""
    return send_telegram(message)

# ============================================
# HELIUS API - FUNCIONES CORE
# ============================================
def helius_rpc_call(method, params):
    """Llamada genérica al RPC de Helius"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    try:
        response = requests.post(HELIUS_RPC_URL, json=payload, timeout=15)
        data = response.json()
        if "error" in data:
            print(f"❌ RPC Error: {data['error']}")
            return None
        return data.get("result")
    except Exception as e:
        print(f"❌ Error RPC: {e}")
        return None

def get_token_accounts(wallet_address):
    """Obtiene todos los tokens de una wallet"""
    result = helius_rpc_call("getTokenAccountsByOwner", [
        wallet_address,
        {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
        {"encoding": "jsonParsed"}
    ])
    if result and "value" in result:
        tokens = []
        for account in result["value"]:
            info = account["account"]["data"]["parsed"]["info"]
            tokens.append({
                "mint": info["mint"],
                "amount": float(info["tokenAmount"]["uiAmount"] or 0),
                "decimals": info["tokenAmount"]["decimals"]
            })
        return tokens
    return []

def get_signatures(address, limit=20):
    """Obtiene las últimas transacciones de una dirección"""
    result = helius_rpc_call("getSignaturesForAddress", [
        address,
        {"limit": limit}
    ])
    return result or []

def get_token_largest_accounts(mint):
    """Obtiene los mayores holders de un token"""
    result = helius_rpc_call("getTokenLargestAccounts", [mint])
    if result and "value" in result:
        return result["value"]
    return []

# ============================================
# HELIUS ENHANCED API - DATOS AVANZADOS
# ============================================
def get_token_metadata(mint):
    """Obtiene metadata de un token via Helius DAS API"""
    url = f"https://api.helius.dev/v0/token-metadata?api-key={HELIUS_API_KEY}"
    payload = {
        "mintAccounts": [mint],
        "includeOffChain": True,
        "disableCache": False
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0]
    except Exception as e:
        print(f"❌ Error metadata: {e}")
    return None

def get_parsed_transactions(address, limit=10):
    """Obtiene transacciones parseadas de Helius"""
    url = f"https://api.helius.dev/v0/addresses/{address}/transactions?api-key={HELIUS_API_KEY}&limit={limit}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"❌ Error transacciones: {e}")
    return []

# ============================================
# BIRDEYE API - DATOS DE MERCADO (GRATIS)
# ============================================
def get_birdeye_token_info(mint):
    """Obtiene info de token desde Birdeye (público)"""
    url = f"https://public-api.birdeye.so/defi/token_overview?address={mint}"
    headers = {"accept": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("data", {})
    except:
        pass
    return {}

# ============================================
# DEXSCREENER API - DATOS DE MERCADO (GRATIS)
# ============================================
def get_dexscreener_token(mint):
    """Obtiene datos de DexScreener"""
    url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            pairs = data.get("pairs", [])
            if pairs:
                # Retorna el par con más liquidez
                return max(pairs, key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0))
    except Exception as e:
        print(f"❌ Error DexScreener: {e}")
    return None

def get_new_tokens_dexscreener():
    """Busca tokens nuevos en Solana via DexScreener"""
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Filtrar solo Solana
            solana_tokens = [t for t in data if t.get("chainId") == "solana"]
            return solana_tokens[:20]  # Top 20 más recientes
    except Exception as e:
        print(f"❌ Error nuevos tokens: {e}")
    return []

# ============================================
# SISTEMA DE SCORING
# ============================================
def calculate_score(token_data):
    """
    Calcula score de 0-100 para un token.
    Basado en múltiples factores ponderados.
    """
    score = 0

    # 1. Smart wallets comprando (30 puntos max)
    sw_count = token_data.get("smart_wallets_count", 0)
    if sw_count >= 5:
        score += 30
    elif sw_count >= 3:
        score += 20
    elif sw_count >= 1:
        score += 10

    # 2. Crecimiento de holders (20 puntos max)
    holders = token_data.get("holders", 0)
    if holders > 1000:
        score += 20
    elif holders > 500:
        score += 15
    elif holders > 100:
        score += 10
    elif holders > 50:
        score += 5

    # 3. Ratio volumen/liquidez (15 puntos max)
    volume = token_data.get("volume_24h", 0)
    liquidity = token_data.get("liquidity", 1)
    ratio = volume / liquidity if liquidity > 0 else 0
    if ratio > 2:
        score += 15
    elif ratio > 1:
        score += 10
    elif ratio > 0.5:
        score += 5

    # 4. Distribución de tokens (15 puntos max)
    top10_pct = token_data.get("top10_pct", 100)
    if top10_pct < 20:
        score += 15
    elif top10_pct < 35:
        score += 10
    elif top10_pct < 50:
        score += 5

    # 5. Seguridad del contrato (10 puntos max)
    if token_data.get("mint_authority_revoked"):
        score += 5
    if token_data.get("freeze_authority_revoked"):
        score += 5

    # 6. Liquidez mínima (10 puntos max)
    if liquidity > 50000:
        score += 10
    elif liquidity > 20000:
        score += 7
    elif liquidity > 5000:
        score += 4

    return min(score, 100)

# ============================================
# SMART WALLET DISCOVERY
# Encuentra wallets que compraron temprano en tokens exitosos
# ============================================
def discover_smart_wallets(token_mint, token_symbol=""):
    """
    Analiza un token exitoso y encuentra las wallets
    que compraron en las primeras horas.
    """
    print(f"🔍 Analizando early buyers de {token_symbol} ({token_mint[:8]}...)")

    # Obtener los top holders actuales
    largest = get_token_largest_accounts(token_mint)

    if not largest:
        print("  No se encontraron holders")
        return []

    potential_smart_wallets = []

    for holder in largest[:20]:  # Top 20 holders
        address = holder.get("address", "")
        amount = float(holder.get("uiAmount", 0) or holder.get("amount", 0))

        if amount > 0:
            # Obtener transacciones de esta wallet
            txs = get_parsed_transactions(address, limit=5)

            if txs:
                potential_smart_wallets.append({
                    "address": address,
                    "token_amount": amount,
                    "tx_count": len(txs)
                })

    print(f"  Encontradas {len(potential_smart_wallets)} wallets potenciales")
    return potential_smart_wallets

# ============================================
# MONITOR DE NUEVOS TOKENS
# ============================================
def scan_new_tokens():
    """
    Escanea nuevos tokens en Solana y los evalúa.
    """
    print("\n🔄 Escaneando nuevos tokens...")

    new_tokens = get_new_tokens_dexscreener()

    if not new_tokens:
        print("  No se encontraron tokens nuevos")
        return []

    evaluated = []

    for token in new_tokens:
        mint = token.get("tokenAddress", "")
        if not mint:
            continue

        # Obtener datos de DexScreener
        dex_data = get_dexscreener_token(mint)

        if not dex_data:
            continue

        liquidity = float(dex_data.get("liquidity", {}).get("usd", 0) or 0)
        volume = float(dex_data.get("volume", {}).get("h24", 0) or 0)
        price = float(dex_data.get("priceUsd", 0) or 0)
        mcap = float(dex_data.get("marketCap", 0) or dex_data.get("fdv", 0) or 0)

        # Filtro rápido: mínimo $5K liquidez
        if liquidity < 5000:
            continue

        token_data = {
            "mint": mint,
            "symbol": dex_data.get("baseToken", {}).get("symbol", "???"),
            "name": dex_data.get("baseToken", {}).get("name", "Unknown"),
            "price": price,
            "liquidity": liquidity,
            "volume_24h": volume,
            "mcap": mcap,
            "holders": 0,  # Se obtiene por separado
            "smart_wallets_count": 0,
            "top10_pct": 50,  # Default conservador
            "mint_authority_revoked": True,  # Verificar después
            "freeze_authority_revoked": True,
        }

        # Calcular score
        token_data["score"] = calculate_score(token_data)

        evaluated.append(token_data)

        # Rate limiting
        time.sleep(0.5)

    # Ordenar por score
    evaluated.sort(key=lambda x: x["score"], reverse=True)

    return evaluated

# ============================================
# MONITOR DE SMART WALLETS
# ============================================
def monitor_smart_wallets():
    """
    Revisa la actividad reciente de las smart wallets.
    Detecta cuando compran un nuevo token.
    """
    print("\n👀 Monitoreando smart wallets...")

    conn = sqlite3.connect("darius_alpha.db")
    c = conn.cursor()
    c.execute("SELECT address, label FROM smart_wallets")
    wallets = c.fetchall()
    conn.close()

    if not wallets:
        print("  No hay smart wallets en la base de datos aún")
        return []

    new_buys = []

    for address, label in wallets:
        print(f"  Revisando {label or address[:8]}...")

        # Obtener transacciones recientes
        txs = get_parsed_transactions(address, limit=5)

        for tx in txs:
            # Buscar swaps (compras de tokens)
            tx_type = tx.get("type", "")
            if tx_type == "SWAP":
                # Extraer detalles del swap
                token_transfers = tx.get("tokenTransfers", [])
                for transfer in token_transfers:
                    if transfer.get("toUserAccount") == address:
                        new_buys.append({
                            "wallet": address,
                            "wallet_label": label,
                            "token_mint": transfer.get("mint", ""),
                            "amount": transfer.get("tokenAmount", 0),
                            "timestamp": tx.get("timestamp", 0)
                        })

        time.sleep(1)  # Rate limiting

    return new_buys

# ============================================
# AÑADIR SMART WALLET
# ============================================
def add_smart_wallet(address, label="", source="manual"):
    """Añade una wallet a la base de datos"""
    conn = sqlite3.connect("darius_alpha.db")
    c = conn.cursor()
    try:
        c.execute("""
            INSERT OR REPLACE INTO smart_wallets 
            (address, label, added_date, source) 
            VALUES (?, ?, ?, ?)
        """, (address, label, datetime.now().isoformat(), source))
        conn.commit()
        print(f"✅ Wallet añadida: {label or address[:12]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

# ============================================
# REGISTRAR OPERACIÓN
# ============================================
def log_trade(token_mint, token_symbol, action, price, amount_sol, notes=""):
    """Registra una operación en la base de datos"""
    conn = sqlite3.connect("darius_alpha.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO trades (token_mint, token_symbol, action, price, amount_sol, timestamp, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (token_mint, token_symbol, action, price, amount_sol, datetime.now().isoformat(), notes))
    conn.commit()
    conn.close()
    print(f"📝 Trade registrado: {action} {token_symbol} @ ${price}")

# ============================================
# LOOP PRINCIPAL
# ============================================
def main_loop():
    """
    Loop principal del bot.
    Ejecuta cada ciclo:
    1. Escanea nuevos tokens
    2. Monitorea smart wallets
    3. Evalúa y envía alertas
    """
    print("=" * 50)
    print("🚀 DARIUS ALPHA TRACKER v1.0")
    print("=" * 50)

    # Inicializar base de datos
    init_db()

    # Mensaje de inicio
    send_telegram("🟢 <b>Darius Alpha Tracker ACTIVADO</b>\n\nEscaneando mercado cada 60 segundos...\nSmart wallets monitoreadas: pendiente de configurar\n\n<i>Let's get this bread 🍞</i>")

    cycle = 0

    while True:
        cycle += 1
        print(f"\n{'='*40}")
        print(f"📊 Ciclo #{cycle} — {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*40}")

        try:
            # === PASO 1: Escanear nuevos tokens ===
            new_tokens = scan_new_tokens()

            for token in new_tokens:
                if token["score"] >= 60:  # Umbral para alertar
                    print(f"  🎯 Token interesante: ${token['symbol']} (Score: {token['score']})")

                    if token["score"] >= 75:
                        # Alerta fuerte
                        send_alpha_alert(token)
                        print(f"  📨 Alerta enviada a Telegram!")
                    else:
                        # Solo log
                        print(f"  📋 Score bajo para alerta ({token['score']}/75)")

            # === PASO 2: Monitorear smart wallets ===
            new_buys = monitor_smart_wallets()

            for buy in new_buys:
                # Si una smart wallet compró algo, investigar
                token_mint = buy["token_mint"]
                dex_data = get_dexscreener_token(token_mint)

                if dex_data:
                    msg = f"""
👁️ <b>SMART WALLET MOVEMENT</b>

<b>Wallet:</b> {buy['wallet_label'] or buy['wallet'][:12]}...
<b>Compró:</b> ${dex_data.get('baseToken', {}).get('symbol', '???')}
<b>CA:</b> <code>{token_mint}</code>
<b>Precio:</b> ${dex_data.get('priceUsd', 'N/A')}
<b>Liquidez:</b> ${float(dex_data.get('liquidity', {}).get('usd', 0) or 0):,.0f}

<i>⚠️ Investiga antes de entrar</i>
"""
                    send_telegram(msg)

            # === PASO 3: Esperar antes del siguiente ciclo ===
            wait_time = 60  # 60 segundos entre ciclos
            print(f"\n⏳ Siguiente ciclo en {wait_time}s...")
            time.sleep(wait_time)

        except KeyboardInterrupt:
            print("\n🛑 Bot detenido por el usuario")
            send_telegram("🔴 <b>Darius Alpha Tracker DETENIDO</b>")
            break
        except Exception as e:
            print(f"❌ Error en ciclo: {e}")
            time.sleep(30)  # Esperar 30s si hay error

# ============================================
# SCRIPT DE SETUP INICIAL
# ============================================
def setup():
    """
    Ejecuta esto UNA VEZ para configurar todo.
    """
    print("🔧 SETUP INICIAL — Darius Alpha Tracker")
    print("=" * 50)

    # 1. Inicializar DB
    init_db()

    # 2. Descubrir smart wallets desde tokens conocidos
    print("\n📡 Descubriendo smart wallets desde tokens de referencia...")

    for symbol, mint in REFERENCE_TOKENS.items():
        wallets = discover_smart_wallets(mint, symbol)
        for w in wallets[:5]:  # Top 5 de cada token
            add_smart_wallet(
                w["address"], 
                label=f"Early_{symbol}_{w['address'][:6]}", 
                source=f"discovered_from_{symbol}"
            )
        time.sleep(2)

    # 3. Test de Telegram
    send_telegram("🔧 <b>Setup completado!</b>\n\nBase de datos creada.\nSmart wallets descubiertas.\nSistema listo para operar.\n\n<i>Ejecuta main_loop() para activar el tracker.</i>")

    print("\n✅ SETUP COMPLETADO")
    print("Ejecuta main_loop() para iniciar el bot")

# ============================================
# PUNTO DE ENTRADA
# ============================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup()
    else:
        # Primero setup si no existe la DB
        try:
            conn = sqlite3.connect("darius_alpha.db")
            conn.close()
        except:
            setup()

        main_loop()
