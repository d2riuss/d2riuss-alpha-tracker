# ============================================
# D2RIUSS ALPHA TRACKER v1.1
# Smart Money Tracker + Alert System for Solana
# By: Darius Marian Burzo
# ============================================

import requests
import json
import time
import sqlite3
import os
from datetime import datetime, timedelta

# ============================================
# CONFIGURACIÓN - TUS DATOS
# ============================================
HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY", "ac619ff6-9d50-4a09-99ff-5a03c556302b")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8648370563:AAEcv5kKvDOMUHcYRFb4IGVE5UicnZdWM88")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1454858664")
HELIUS_RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
HELIUS_API_URL = f"https://api.helius.xyz/v0"

# ============================================
# TOKENS SEMILLA - Los que explotaron
# El bot analizará los early buyers de estos tokens
# y los guardará como smart wallets
# ============================================
SEED_TOKENS = {
    "TRUMP": "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN",
    "CHILLGUY": "Df6yfrKC8kZE3KNkrHERKzAetSxbrWeniQfyJY4Jpump",
    "MLG": "4mfnGYRKTBJRMFKWnmBFbMFohnUNBLKKQxpump",
}

# ============================================
# CONFIGURACIÓN DE SCORING
# ============================================
SCORING_WEIGHTS = {
    "smart_wallets": 30,      # Cuántas smart wallets compraron
    "liquidity": 15,          # Liquidez del pool
    "holders": 10,            # Número de holders
    "mint_revoked": 15,       # Mint authority revocada
    "freeze_revoked": 10,     # Freeze authority revocada
    "top10_distribution": 10, # Distribución top 10 holders
    "volume_ratio": 10,       # Ratio volumen/liquidez
}

# ============================================
# BASE DE DATOS LOCAL
# ============================================
def init_db():
    conn = sqlite3.connect("d2riuss_alpha.db")
    c = conn.cursor()

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
    score = token_data.get("score", 0)

    if score >= 85:
        emoji = "🔥🔥🔥"
    elif score >= 70:
        emoji = "🔥🔥"
    else:
        emoji = "🔥"

    mint_check = "✅" if token_data.get("mint_authority_revoked") else "❌"
    freeze_check = "✅" if token_data.get("freeze_authority_revoked") else "❌"
    top10_check = "✅" if token_data.get("top10_pct", 100) < 40 else "❌"
    liq_check = "✅" if token_data.get("liquidity", 0) > 5000 else "❌"

    message = f"""
{emoji} <b>D2RIUSS ALPHA ALERT — Score: {score}/100</b>

<b>Token:</b> ${token_data.get('symbol', 'N/A')}
<b>CA:</b> <code>{token_data.get('mint', 'N/A')}</code>
<b>Precio:</b> ${token_data.get('price', 'N/A')}
<b>Liquidez:</b> ${token_data.get('liquidity', 0):,.0f}
<b>Holders:</b> {token_data.get('holders', 'N/A')}
<b>Market Cap:</b> ${token_data.get('mcap', 0):,.0f}

<b>Smart Wallets dentro:</b> {token_data.get('smart_wallets_count', 0)}

<b>Filtros de seguridad:</b>
{mint_check} Mint authority revocada
{freeze_check} Freeze authority revocada
{top10_check} Top 10 holders < 40%
{liq_check} Liquidez > $5K

<b>⚡ Acción sugerida:</b> {'ENTRADA con 10-15€' if score >= 75 else 'OBSERVAR'}
🎯 TP1: 3x | TP2: 10x | SL: -40%

<i>— D2RIUSS Alpha Tracker v1.1</i>
"""
    return send_telegram(message)

# ============================================
# HELIUS API - FUNCIONES CORE
# ============================================
def helius_rpc_call(method, params):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    try:
        response = requests.post(HELIUS_RPC_URL, json=payload, timeout=30)
        data = response.json()
        if "error" in data:
            print(f"  ⚠️ RPC Error: {data['error']}")
            return None
        return data.get("result")
    except Exception as e:
        print(f"  ❌ RPC Error: {e}")
        return None

def helius_api_call(endpoint, params=None):
    url = f"{HELIUS_API_URL}/{endpoint}?api-key={HELIUS_API_KEY}"
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ⚠️ API Error {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"  ❌ API Error: {e}")
        return None

def get_token_metadata(mint):
    url = f"{HELIUS_API_URL}/token-metadata?api-key={HELIUS_API_KEY}"
    payload = {
        "mintAccounts": [mint],
        "includeOffChain": True,
        "disableCache": False
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0]
        return None
    except Exception as e:
        print(f"  ❌ Metadata Error: {e}")
        return None

# ============================================
# BIRDEYE / DEXSCREENER - DATOS DE MERCADO
# ============================================
def get_dexscreener_data(mint):
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            pairs = data.get("pairs", [])
            if pairs:
                pair = pairs[0]
                return {
                    "price": float(pair.get("priceUsd", 0) or 0),
                    "liquidity": float(pair.get("liquidity", {}).get("usd", 0) or 0),
                    "mcap": float(pair.get("marketCap", 0) or 0),
                    "volume_24h": float(pair.get("volume", {}).get("h24", 0) or 0),
                    "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0) or 0),
                    "pair_address": pair.get("pairAddress", ""),
                    "dex": pair.get("dexId", ""),
                    "name": pair.get("baseToken", {}).get("name", "Unknown"),
                    "symbol": pair.get("baseToken", {}).get("symbol", "???"),
                }
        return None
    except Exception as e:
        print(f"  ❌ DexScreener Error: {e}")
        return None

# ============================================
# SMART WALLET DISCOVERY
# ============================================
def discover_smart_wallets(token_mint, token_symbol=""):
    print(f"  🔍 Analizando early buyers de {token_symbol} ({token_mint[:8]}...)")

    # Obtener las primeras transacciones del token usando Helius
    signatures = helius_rpc_call("getSignaturesForAddress", [
        token_mint,
        {"limit": 50}
    ])

    if not signatures:
        print(f"  ⚠️ No se encontraron transacciones para {token_symbol}")
        # Intentar con parsed transaction history
        parsed = helius_api_call(f"addresses/{token_mint}/transactions", {"limit": 50})
        if parsed:
            wallets = set()
            for tx in parsed:
                if tx.get("type") in ["SWAP", "TRANSFER"]:
                    for acc in tx.get("accountData", []):
                        if acc.get("nativeBalanceChange", 0) < 0:
                            wallets.add(acc.get("account", ""))

            wallet_list = [{"address": w, "tx_count": 1} for w in wallets if w and len(w) > 30]
            print(f"  ✅ Encontradas {len(wallet_list)} wallets desde parsed history")
            return wallet_list[:10]
        return []

    # Analizar las transacciones para encontrar compradores
    wallets = {}
    for sig_info in signatures[:30]:
        sig = sig_info.get("signature", "")
        if not sig:
            continue

        # Obtener detalle de la transacción
        tx_detail = helius_rpc_call("getTransaction", [
            sig,
            {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
        ])

        if not tx_detail:
            continue

        # Extraer las cuentas involucradas
        try:
            account_keys = tx_detail.get("transaction", {}).get("message", {}).get("accountKeys", [])
            for acc in account_keys:
                if isinstance(acc, dict):
                    pubkey = acc.get("pubkey", "")
                elif isinstance(acc, str):
                    pubkey = acc
                else:
                    continue

                if pubkey and len(pubkey) > 30 and pubkey != token_mint:
                    if pubkey not in wallets:
                        wallets[pubkey] = {"address": pubkey, "tx_count": 0}
                    wallets[pubkey]["tx_count"] += 1
        except Exception as e:
            continue

        time.sleep(0.2)  # Rate limiting

    # Ordenar por número de transacciones
    sorted_wallets = sorted(wallets.values(), key=lambda x: x["tx_count"], reverse=True)

    # Filtrar wallets del sistema (programas, etc.)
    system_programs = [
        "11111111111111111111111111111111",
        "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
        "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL",
        "ComputeBudget111111111111111111111111111111",
        "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",
    ]

    filtered = [w for w in sorted_wallets if w["address"] not in system_programs]

    print(f"  ✅ Encontradas {len(filtered)} wallets potenciales para {token_symbol}")
    return filtered[:10]

def add_smart_wallet(address, label="", source="manual"):
    conn = sqlite3.connect("d2riuss_alpha.db")
    c = conn.cursor()
    try:
        c.execute("""
            INSERT OR IGNORE INTO smart_wallets (address, label, added_date, source)
            VALUES (?, ?, ?, ?)
        """, (address, label, datetime.now().isoformat(), source))
        conn.commit()
        if c.rowcount > 0:
            print(f"  ➕ Smart wallet añadida: {label} ({address[:8]}...)")
    except Exception as e:
        print(f"  ❌ Error añadiendo wallet: {e}")
    finally:
        conn.close()

def get_smart_wallets():
    conn = sqlite3.connect("d2riuss_alpha.db")
    c = conn.cursor()
    c.execute("SELECT address, label FROM smart_wallets")
    wallets = c.fetchall()
    conn.close()
    return wallets

# ============================================
# TOKEN ANALYSIS & SCORING
# ============================================
def analyze_token(mint):
    print(f"  📊 Analizando token {mint[:8]}...")

    # Datos de DexScreener
    dex_data = get_dexscreener_data(mint)
    if not dex_data:
        return None

    # Datos de metadata
    metadata = get_token_metadata(mint)

    # Verificar mint/freeze authority
    token_info = helius_rpc_call("getAccountInfo", [
        mint,
        {"encoding": "jsonParsed"}
    ])

    mint_revoked = False
    freeze_revoked = False

    if token_info and token_info.get("value"):
        parsed = token_info["value"].get("data", {}).get("parsed", {}).get("info", {})
        mint_revoked = parsed.get("mintAuthority") is None
        freeze_revoked = parsed.get("freezeAuthority") is None

    # Obtener holders (top 20)
    holders_data = helius_rpc_call("getTokenLargestAccounts", [mint])

    top10_pct = 100
    holder_count = 0
    if holders_data and holders_data.get("value"):
        accounts = holders_data["value"]
        holder_count = len(accounts)
        total_supply = sum(float(a.get("amount", 0)) for a in accounts)
        if total_supply > 0:
            top10_supply = sum(float(a.get("amount", 0)) for a in accounts[:10])
            top10_pct = (top10_supply / total_supply) * 100

    # Verificar smart wallets
    smart_wallets = get_smart_wallets()
    smart_count = 0

    if holders_data and holders_data.get("value"):
        holder_addresses = set()
        for account in holders_data["value"]:
            addr = account.get("address", "")
            if addr:
                holder_addresses.add(addr)

        for sw_address, sw_label in smart_wallets:
            if sw_address in holder_addresses:
                smart_count += 1

    # SCORING
    score = 0

    # Smart wallets (0-30 puntos)
    if smart_count >= 3:
        score += 30
    elif smart_count >= 2:
        score += 20
    elif smart_count >= 1:
        score += 10

    # Liquidez (0-15 puntos)
    liq = dex_data.get("liquidity", 0)
    if liq >= 50000:
        score += 15
    elif liq >= 20000:
        score += 12
    elif liq >= 10000:
        score += 8
    elif liq >= 5000:
        score += 5

    # Holders (0-10 puntos)
    if holder_count >= 100:
        score += 10
    elif holder_count >= 50:
        score += 7
    elif holder_count >= 20:
        score += 4

    # Mint revoked (0-15 puntos)
    if mint_revoked:
        score += 15

    # Freeze revoked (0-10 puntos)
    if freeze_revoked:
        score += 10

    # Top 10 distribution (0-10 puntos)
    if top10_pct < 20:
        score += 10
    elif top10_pct < 30:
        score += 7
    elif top10_pct < 40:
        score += 4

    # Volume ratio (0-10 puntos)
    vol = dex_data.get("volume_24h", 0)
    if liq > 0 and vol / liq > 2:
        score += 10
    elif liq > 0 and vol / liq > 1:
        score += 7
    elif liq > 0 and vol / liq > 0.5:
        score += 4

    token_analysis = {
        "mint": mint,
        "name": dex_data.get("name", "Unknown"),
        "symbol": dex_data.get("symbol", "???"),
        "price": dex_data.get("price", 0),
        "liquidity": liq,
        "mcap": dex_data.get("mcap", 0),
        "volume_24h": vol,
        "holders": holder_count,
        "mint_authority_revoked": mint_revoked,
        "freeze_authority_revoked": freeze_revoked,
        "top10_pct": top10_pct,
        "smart_wallets_count": smart_count,
        "score": score,
    }

    return token_analysis

# ============================================
# NEW TOKEN SCANNER
# ============================================
def scan_new_tokens():
    print("  🔎 Escaneando nuevos tokens...")

    # Buscar tokens recientes en DexScreener (Solana)
    try:
        url = "https://api.dexscreener.com/token-profiles/latest/v1"
        response = requests.get(url, timeout=15)

        if response.status_code != 200:
            print(f"  ⚠️ DexScreener profiles error: {response.status_code}")
            return []

        profiles = response.json()

        # Filtrar solo Solana
        solana_tokens = [p for p in profiles if p.get("chainId") == "solana"]

        new_tokens = []
        for token in solana_tokens[:10]:  # Analizar top 10
            mint = token.get("tokenAddress", "")
            if not mint:
                continue

            # Verificar si ya lo tenemos
            conn = sqlite3.connect("d2riuss_alpha.db")
            c = conn.cursor()
            c.execute("SELECT mint FROM detected_tokens WHERE mint = ?", (mint,))
            exists = c.fetchone()
            conn.close()

            if exists:
                continue

            new_tokens.append(mint)

        return new_tokens

    except Exception as e:
        print(f"  ❌ Error escaneando: {e}")
        return []

# ============================================
# SMART WALLET MONITOR
# ============================================
def monitor_smart_wallets():
    print("  👁️ Monitoreando smart wallets...")

    wallets = get_smart_wallets()
    if not wallets:
        print("  No hay smart wallets en la base de datos aún")
        return []

    print(f"  📡 Monitoreando {len(wallets)} smart wallets...")

    new_tokens_found = set()

    for address, label in wallets[:20]:  # Limitar a 20 para no exceder rate limits
        try:
            # Obtener transacciones recientes
            parsed = helius_api_call(f"addresses/{address}/transactions", {"limit": 5})

            if not parsed:
                continue

            for tx in parsed:
                tx_type = tx.get("type", "")
                if tx_type in ["SWAP", "TRANSFER"]:
                    # Buscar tokens nuevos en la transacción
                    for event in tx.get("tokenTransfers", []):
                        token_mint = event.get("mint", "")
                        if token_mint and len(token_mint) > 30:
                            new_tokens_found.add(token_mint)

            time.sleep(0.3)  # Rate limiting

        except Exception as e:
            print(f"  ⚠️ Error monitoreando {label}: {e}")
            continue

    if new_tokens_found:
        print(f"  🎯 {len(new_tokens_found)} tokens encontrados en smart wallets")

    return list(new_tokens_found)

# ============================================
# SETUP - DESCUBRIR SMART WALLETS INICIALES
# ============================================
def run_setup():
    print("")
    print("=" * 50)
    print("🔧 D2RIUSS ALPHA TRACKER — SETUP INICIAL")
    print("=" * 50)

    init_db()

    print("")
    print("📡 Descubriendo smart wallets desde tokens semilla...")
    print("")

    total_wallets = 0

    for symbol, mint in SEED_TOKENS.items():
        print(f"🪙 Procesando {symbol}...")
        wallets = discover_smart_wallets(mint, symbol)

        added = 0
        for w in wallets[:5]:  # Top 5 de cada token
            add_smart_wallet(
                w["address"],
                label=f"Early_{symbol}_{w['address'][:6]}",
                source=f"seed_{symbol}"
            )
            added += 1

        total_wallets += added
        print(f"  ✅ {added} wallets añadidas de {symbol}")
        print("")
        time.sleep(2)

    # Verificar cuántas tenemos
    all_wallets = get_smart_wallets()

    send_telegram(f"""
🔧 <b>D2RIUSS ALPHA TRACKER v1.1 — Setup Completado!</b>

✅ Base de datos creada
✅ {len(all_wallets)} smart wallets descubiertas
✅ Tokens semilla analizados: {', '.join(SEED_TOKENS.keys())}

<b>El bot está activo y escaneando 24/7</b>
Te llegarán alertas cuando detecte oportunidades.

<i>— D2RIUSS Alpha Tracker v1.1</i>
""")

    print("=" * 50)
    print(f"✅ SETUP COMPLETADO — {len(all_wallets)} smart wallets en la DB")
    print("=" * 50)

# ============================================
# MAIN LOOP
# ============================================
def main_loop():
    print("")
    print("=" * 50)
    print("🚀 D2RIUSS ALPHA TRACKER v1.1")
    print("=" * 50)

    # Verificar si necesita setup
    needs_setup = True
    try:
        conn = sqlite3.connect("d2riuss_alpha.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM smart_wallets")
        count = c.fetchone()[0]
        conn.close()
        if count > 0:
            needs_setup = False
            print(f"✅ Base de datos cargada — {count} smart wallets")
    except:
        needs_setup = True

    if needs_setup:
        run_setup()

    init_db()

    send_telegram("""
🚀 <b>D2RIUSS ALPHA TRACKER v1.1 — ONLINE</b>

El bot está activo y escaneando.
Recibirás alertas cuando detecte oportunidades.

<i>— D2RIUSS Alpha Tracker v1.1</i>
""")

    cycle = 0

    while True:
        cycle += 1
        now = datetime.now().strftime("%H:%M:%S")

        print("")
        print("=" * 45)
        print(f"  📊 Ciclo #{cycle} — {now}")
        print("=" * 45)
        print("")

        try:
            # FASE 1: Escanear nuevos tokens
            print("🔎 Escaneando nuevos tokens...")
            new_tokens = scan_new_tokens()

            if new_tokens:
                print(f"  📋 {len(new_tokens)} tokens nuevos encontrados")
            else:
                print("  No hay tokens nuevos")

            # FASE 2: Monitorear smart wallets
            print("")
            sw_tokens = monitor_smart_wallets()

            # Combinar tokens encontrados
            all_tokens = list(set(new_tokens + sw_tokens))

            # FASE 3: Analizar tokens prometedores
            if all_tokens:
                print(f"")
                print(f"📊 Analizando {len(all_tokens)} tokens...")

                for mint in all_tokens[:5]:  # Máximo 5 por ciclo
                    analysis = analyze_token(mint)

                    if analysis:
                        score = analysis["score"]
                        symbol = analysis["symbol"]

                        print(f"  {symbol}: Score {score}/100")

                        # Guardar en DB
                        conn = sqlite3.connect("d2riuss_alpha.db")
                        c = conn.cursor()
                        c.execute("""
                            INSERT OR REPLACE INTO detected_tokens 
                            (mint, name, symbol, score, smart_wallets_in, liquidity, 
                             holders, mint_authority_revoked, freeze_authority_revoked,
                             top10_holder_pct, detected_at, price_at_detection)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            analysis["mint"], analysis["name"], analysis["symbol"],
                            score, analysis["smart_wallets_count"], analysis["liquidity"],
                            analysis["holders"], analysis["mint_authority_revoked"],
                            analysis["freeze_authority_revoked"], analysis["top10_pct"],
                            datetime.now().isoformat(), analysis["price"]
                        ))
                        conn.commit()
                        conn.close()

                        # Alertar si score >= 60
                        if score >= 60:
                            print(f"  🔥 ALERTA! {symbol} score {score}")
                            send_alpha_alert(analysis)

                    time.sleep(1)

            # Resumen del ciclo
            wallets = get_smart_wallets()
            print(f"")
            print(f"📈 Resumen: {len(wallets)} smart wallets | {len(all_tokens)} tokens analizados")

        except Exception as e:
            print(f"❌ Error en ciclo {cycle}: {e}")
            send_telegram(f"⚠️ Error en ciclo {cycle}: {str(e)[:200]}")

        # Esperar 60 segundos
        print(f"")
        print(f"⏳ Siguiente ciclo en 60s...")
        time.sleep(60)

# ============================================
# PUNTO DE ENTRADA
# ============================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        init_db()
        run_setup()
    else:
        main_loop()
