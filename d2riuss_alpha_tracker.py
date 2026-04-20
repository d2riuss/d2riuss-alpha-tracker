# ============================================
# D2RIUSS ALPHA TRACKER v1.2
# Smart Money Tracker + Alert System for Solana
# By: Darius Marian Burzo
# ============================================
# CHANGELOG v1.2:
# - Añadidas 7 wallets de élite verificadas
# - Nuevo sistema de wallets predefinidas (ELITE_WALLETS)
# - Se cargan automáticamente al iniciar
# - Más cobertura = más alertas
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
# ============================================
SEED_TOKENS = {
    "TRUMP": "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN",
    "CHILLGUY": "Df6yfrKC8kZE3KNkrHERKzAetSxbrWeniQfyJY4Jpump",
    "MLG": "4mfnGYRKTBJRMFKWnmBFbMFohnUNBLKKQxpump",
}

# ============================================
# WALLETS DE ÉLITE - Verificadas con alto ROI
# Fuentes: GMGN, Nansen, Dune, KOLScan
# ============================================
ELITE_WALLETS = {
    "AVAZvHLR2PcWpDf8BXY4rVxNHYRBytycHkcB5z5QNXYm": {
        "label": "ELITE_PumpFun_Sniper",
        "source": "elite_gmgn",
        "profile": "Alto win rate en Pump.fun"
    },
    "4Be9CvxqHW6BYiRAxW9Q3xu1ycTMWaL5z8NX4HR3ha7t": {
        "label": "ELITE_50x_Flipper",
        "source": "elite_gmgn",
        "profile": "Flips de 50x+ en Raydium"
    },
    "8zFZHuSRuDpuAR7J6FzwyF3vKNx4CVW3DFHJerQhc7Zd": {
        "label": "ELITE_Insider_Signals",
        "source": "elite_nansen",
        "profile": "Smart money / insider signals"
    },
    "H72yLkhTnoBfhBTXXaj1RBXuirm8s8G5fcVh2XpQLggM": {
        "label": "ELITE_HighVol_Whale",
        "source": "elite_nansen",
        "profile": "Whale con volumen alto, pocos rugs"
    },
    "4EtAJ1p8RjqccEVhEhaYnEgQ6kA4JHR8oYqyLFwARUj6": {
        "label": "ELITE_44M_TRUMP_Whale",
        "source": "elite_dune",
        "profile": "$44M profit — 292% ROI en TRUMP"
    },
    "HWdeCUjBvPP1HJ5oCJt7aNsvMWpWoDgiejUWvfFX6T7R": {
        "label": "ELITE_Memecoin_Whale",
        "source": "elite_dune",
        "profile": "Whale memecoin — $4.38M profit"
    },
    "fwHknyxZTgFGytVz9VPrvWqipW2V4L4D99gEb831t81": {
        "label": "ELITE_AI16Z_1360pct",
        "source": "elite_kolscan",
        "profile": "1,360% ROI en AI16Z"
    },
}

# ============================================
# CONFIGURACIÓN DE SCORING
# ============================================
SCORING_WEIGHTS = {
    "smart_wallets": 30,
    "liquidity": 15,
    "holders": 10,
    "mint_revoked": 15,
    "freeze_revoked": 10,
    "top10_distribution": 10,
    "volume_ratio": 10,
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
# CARGAR WALLETS DE ÉLITE EN LA DB
# ============================================
def load_elite_wallets():
    """Carga las wallets de élite predefinidas en la base de datos"""
    conn = sqlite3.connect("d2riuss_alpha.db")
    c = conn.cursor()

    added = 0
    for address, info in ELITE_WALLETS.items():
        c.execute("SELECT address FROM smart_wallets WHERE address = ?", (address,))
        if not c.fetchone():
            c.execute("""
                INSERT INTO smart_wallets (address, label, added_date, source)
                VALUES (?, ?, ?, ?)
            """, (address, info["label"], datetime.now().isoformat(), info["source"]))
            added += 1
            print(f"  🐋 Añadida: {info['label']} — {info['profile']}")

    conn.commit()
    conn.close()

    if added > 0:
        print(f"  ✅ {added} wallets de élite añadidas")
    else:
        print(f"  ℹ️ Wallets de élite ya estaban en la DB")

    return added

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

<i>— D2RIUSS Alpha Tracker v1.2</i>
"""
    return send_telegram(message)

# ============================================
# HELIUS API - FUNCIONES DE BLOCKCHAIN
# ============================================
def get_token_metadata(mint):
    url = f"{HELIUS_API_URL}/token-metadata?api-key={HELIUS_API_KEY}"
    try:
        response = requests.post(url, json={"mintAccounts": [mint]}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0]
    except Exception as e:
        print(f"  ⚠️ Error metadata {mint[:8]}...: {e}")
    return None

def get_token_holders(mint, limit=20):
    url = HELIUS_RPC_URL
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenLargestAccounts",
        "params": [mint]
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            result = response.json().get("result", {})
            return result.get("value", [])
    except Exception as e:
        print(f"  ⚠️ Error holders {mint[:8]}...: {e}")
    return []

def get_wallet_transactions(wallet, limit=10):
    url = f"{HELIUS_API_URL}/addresses/{wallet}/transactions?api-key={HELIUS_API_KEY}&limit={limit}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"  ⚠️ Error txs {wallet[:8]}...: {e}")
    return []

def get_wallet_token_accounts(wallet):
    url = HELIUS_RPC_URL
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            wallet,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed"}
        ]
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            result = response.json().get("result", {})
            return result.get("value", [])
    except Exception as e:
        print(f"  ⚠️ Error token accounts {wallet[:8]}...: {e}")
    return []

# ============================================
# DEXSCREENER API - DATOS DE MERCADO
# ============================================
def get_dexscreener_data(mint):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            pairs = data.get("pairs", [])
            if pairs:
                pair = pairs[0]
                return {
                    "price": float(pair.get("priceUsd", 0) or 0),
                    "liquidity": float(pair.get("liquidity", {}).get("usd", 0) or 0),
                    "volume_24h": float(pair.get("volume", {}).get("h24", 0) or 0),
                    "mcap": float(pair.get("marketCap", 0) or 0),
                    "price_change_1h": float(pair.get("priceChange", {}).get("h1", 0) or 0),
                    "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0) or 0),
                    "pair_created": pair.get("pairCreatedAt", ""),
                    "name": pair.get("baseToken", {}).get("name", "Unknown"),
                    "symbol": pair.get("baseToken", {}).get("symbol", "???"),
                    "dex": pair.get("dexId", "unknown"),
                }
    except Exception as e:
        print(f"  ⚠️ Error DexScreener {mint[:8]}...: {e}")
    return None

def scan_new_tokens():
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    new_mints = []
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            tokens = response.json()
            for token in tokens[:20]:
                if token.get("chainId") == "solana":
                    mint = token.get("tokenAddress", "")
                    if mint:
                        new_mints.append(mint)
    except Exception as e:
        print(f"  ⚠️ Error escaneando nuevos tokens: {e}")
    return new_mints

# ============================================
# SMART WALLET MANAGEMENT
# ============================================
def add_smart_wallet(address, label="Unknown", source="auto"):
    conn = sqlite3.connect("d2riuss_alpha.db")
    c = conn.cursor()
    c.execute("SELECT address FROM smart_wallets WHERE address = ?", (address,))
    if not c.fetchone():
        c.execute("""
            INSERT INTO smart_wallets (address, label, added_date, source)
            VALUES (?, ?, ?, ?)
        """, (address, label, datetime.now().isoformat(), source))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def get_smart_wallets():
    conn = sqlite3.connect("d2riuss_alpha.db")
    c = conn.cursor()
    c.execute("SELECT address, label, source FROM smart_wallets")
    wallets = [{"address": row[0], "label": row[1], "source": row[2]} for row in c.fetchall()]
    conn.close()
    return wallets

# ============================================
# MONITOR SMART WALLETS
# ============================================
def monitor_smart_wallets():
    wallets = get_smart_wallets()
    detected_tokens = []

    if not wallets:
        print("  ⚠️ No hay smart wallets en la DB")
        return []

    print(f"  👁️ Monitoreando {len(wallets)} smart wallets...")

    # Monitorear un subconjunto por ciclo para no gastar API
    wallets_to_check = wallets[:5]  # 5 por ciclo, rotando

    for wallet in wallets_to_check:
        try:
            txs = get_wallet_transactions(wallet["address"], limit=5)

            for tx in txs:
                if tx.get("type") == "SWAP":
                    token_transfers = tx.get("tokenTransfers", [])
                    for transfer in token_transfers:
                        mint = transfer.get("mint", "")
                        if mint and mint not in detected_tokens:
                            detected_tokens.append(mint)
                            print(f"    🎯 {wallet['label']}: compró {mint[:12]}...")

            time.sleep(0.5)
        except Exception as e:
            print(f"    ⚠️ Error monitoreando {wallet['label']}: {e}")

    return detected_tokens

# ============================================
# ANÁLISIS Y SCORING DE TOKENS
# ============================================
def analyze_token(mint):
    # Obtener datos de DexScreener
    dex_data = get_dexscreener_data(mint)
    if not dex_data:
        return None

    # Filtro rápido: descartar tokens sin liquidez
    if dex_data["liquidity"] < 1000:
        return None

    score = 0

    # 1. Smart wallets que compraron (30 pts)
    wallets = get_smart_wallets()
    sw_count = 0

    for wallet in wallets[:10]:
        try:
            accounts = get_wallet_token_accounts(wallet["address"])
            for acc in accounts:
                parsed = acc.get("account", {}).get("data", {}).get("parsed", {})
                info = parsed.get("info", {})
                if info.get("mint") == mint:
                    amount = float(info.get("tokenAmount", {}).get("uiAmount", 0) or 0)
                    if amount > 0:
                        sw_count += 1
                        break
        except:
            pass
        time.sleep(0.3)

    if sw_count >= 3:
        score += 30
    elif sw_count >= 2:
        score += 20
    elif sw_count >= 1:
        score += 10

    # 2. Liquidez (15 pts)
    liq = dex_data["liquidity"]
    if liq >= 50000:
        score += 15
    elif liq >= 20000:
        score += 12
    elif liq >= 10000:
        score += 8
    elif liq >= 5000:
        score += 5

    # 3. Holders (10 pts)
    holders = get_token_holders(mint)
    num_holders = len(holders)
    if num_holders >= 100:
        score += 10
    elif num_holders >= 50:
        score += 7
    elif num_holders >= 20:
        score += 4

    # 4. Mint authority (15 pts)
    mint_revoked = False
    try:
        metadata = get_token_metadata(mint)
        if metadata:
            on_chain = metadata.get("onChainAccountInfo", {}).get("accountInfo", {}).get("data", {}).get("parsed", {}).get("info", {})
            mint_auth = on_chain.get("mintAuthority")
            freeze_auth = on_chain.get("freezeAuthority")
            mint_revoked = mint_auth is None
            freeze_revoked = freeze_auth is None
            if mint_revoked:
                score += 15
            if freeze_revoked:
                score += 10
    except:
        freeze_revoked = False

    # 5. Top 10 distribution (10 pts)
    top10_pct = 0
    if holders:
        total_supply = sum(float(h.get("amount", 0)) for h in holders)
        if total_supply > 0:
            top10_amount = sum(float(h.get("amount", 0)) for h in holders[:10])
            top10_pct = (top10_amount / total_supply) * 100
            if top10_pct < 30:
                score += 10
            elif top10_pct < 50:
                score += 6
            elif top10_pct < 70:
                score += 3

    # 6. Volume ratio (10 pts)
    if liq > 0:
        vol_ratio = dex_data["volume_24h"] / liq
        if vol_ratio >= 2:
            score += 10
        elif vol_ratio >= 1:
            score += 7
        elif vol_ratio >= 0.5:
            score += 4

    return {
        "mint": mint,
        "name": dex_data["name"],
        "symbol": dex_data["symbol"],
        "price": dex_data["price"],
        "liquidity": dex_data["liquidity"],
        "volume_24h": dex_data["volume_24h"],
        "mcap": dex_data["mcap"],
        "holders": num_holders,
        "smart_wallets_count": sw_count,
        "mint_authority_revoked": mint_revoked,
        "freeze_authority_revoked": freeze_revoked,
        "top10_pct": top10_pct,
        "score": min(score, 100),
    }

# ============================================
# DESCUBRIR SMART WALLETS DESDE TOKENS SEMILLA
# ============================================
def discover_wallets_from_seed(mint, symbol):
    print(f"  🔍 Analizando early buyers de {symbol}...")

    holders = get_token_holders(mint, limit=20)
    if not holders:
        print(f"    ⚠️ No se pudieron obtener holders de {symbol}")
        return []

    discovered = []

    for holder in holders[:15]:
        try:
            owner_address = holder.get("address", "")
            if not owner_address:
                continue

            # Resolver el owner real de la token account
            url = HELIUS_RPC_URL
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [owner_address, {"encoding": "jsonParsed"}]
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                result = response.json().get("result", {})
                value = result.get("value", {})
                if value:
                    data = value.get("data", {})
                    if isinstance(data, dict):
                        parsed = data.get("parsed", {})
                        info = parsed.get("info", {})
                        owner = info.get("owner", "")
                        if owner and len(owner) > 30:
                            discovered.append({
                                "address": owner,
                                "amount": float(holder.get("amount", 0))
                            })

            time.sleep(0.5)
        except Exception as e:
            continue

    return discovered

# ============================================
# SETUP INICIAL - DESCUBRIR WALLETS + CARGAR ÉLITE
# ============================================
def run_setup():
    print("")
    print("=" * 50)
    print("🔧 D2RIUSS ALPHA TRACKER v1.2 — SETUP")
    print("=" * 50)
    print("")

    init_db()

    # PASO 1: Cargar wallets de élite
    print("🐋 Cargando wallets de élite verificadas...")
    elite_added = load_elite_wallets()
    print("")

    # PASO 2: Descubrir wallets desde tokens semilla
    print("🔍 Descubriendo wallets desde tokens semilla...")
    total_seed_wallets = 0

    for symbol, mint in SEED_TOKENS.items():
        print(f"  📊 Procesando {symbol}...")

        discovered = discover_wallets_from_seed(mint, symbol)

        if not discovered:
            print(f"    ⚠️ No se encontraron wallets para {symbol}")
            continue

        # Ordenar por cantidad (los que más tienen)
        discovered.sort(key=lambda x: x["amount"], reverse=True)

        # Añadir top 5 como smart wallets
        added = 0
        for w in discovered[:5]:
            result = add_smart_wallet(
                w["address"],
                label=f"Early_{symbol}_{w['address'][:6]}",
                source=f"seed_{symbol}"
            )
            if result:
                added += 1

        total_seed_wallets += added
        print(f"  ✅ {added} wallets añadidas de {symbol}")
        time.sleep(2)

    # Verificar total
    all_wallets = get_smart_wallets()

    # Contar por tipo
    elite_count = sum(1 for w in all_wallets if w["source"].startswith("elite"))
    seed_count = sum(1 for w in all_wallets if w["source"].startswith("seed"))

    send_telegram(f"""
🔧 <b>D2RIUSS ALPHA TRACKER v1.2 — Setup Completado!</b>

✅ Base de datos creada
🐋 {elite_count} wallets de élite cargadas
🔍 {seed_count} wallets descubiertas de tokens semilla
📊 <b>Total: {len(all_wallets)} smart wallets rastreando</b>

<b>Wallets de élite incluidas:</b>
• ELITE_PumpFun_Sniper
• ELITE_50x_Flipper
• ELITE_Insider_Signals
• ELITE_HighVol_Whale
• ELITE_44M_TRUMP_Whale ($44M profit)
• ELITE_Memecoin_Whale ($4.38M profit)
• ELITE_AI16Z_1360pct (1,360% ROI)

<b>El bot está activo y escaneando 24/7</b>
Te llegarán alertas cuando detecte oportunidades.

<i>— D2RIUSS Alpha Tracker v1.2</i>
""")

    print("")
    print("=" * 50)
    print(f"✅ SETUP COMPLETADO — {len(all_wallets)} smart wallets en la DB")
    print(f"   🐋 {elite_count} élite | 🔍 {seed_count} semilla")
    print("=" * 50)

# ============================================
# MAIN LOOP
# ============================================
def main_loop():
    print("")
    print("=" * 50)
    print("🚀 D2RIUSS ALPHA TRACKER v1.2")
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

            # Siempre verificar que las élite estén cargadas
            init_db()
            new_elite = load_elite_wallets()
            if new_elite > 0:
                print(f"  🐋 {new_elite} nuevas wallets de élite añadidas")
    except:
        needs_setup = True

    if needs_setup:
        run_setup()

    init_db()

    # Contar wallets por tipo
    all_wallets = get_smart_wallets()
    elite_count = sum(1 for w in all_wallets if w["source"].startswith("elite"))
    seed_count = sum(1 for w in all_wallets if w["source"].startswith("seed"))

    send_telegram(f"""
🚀 <b>D2RIUSS ALPHA TRACKER v1.2 — ONLINE</b>

📊 <b>{len(all_wallets)} smart wallets rastreando</b>
🐋 {elite_count} wallets de élite
🔍 {seed_count} wallets de tokens semilla

El bot está activo y escaneando.
Recibirás alertas cuando detecte oportunidades.

<i>— D2RIUSS Alpha Tracker v1.2</i>
""")

    cycle = 0
    wallet_rotation_index = 0

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

            # FASE 2: Monitorear smart wallets (con rotación)
            print("")
            wallets = get_smart_wallets()

            if wallets:
                # Rotar qué wallets monitoreamos cada ciclo
                batch_size = 5
                start = wallet_rotation_index % len(wallets)
                end = min(start + batch_size, len(wallets))
                wallets_batch = wallets[start:end]

                if end < start + batch_size:
                    wallets_batch += wallets[:batch_size - len(wallets_batch)]

                wallet_rotation_index += batch_size

                print(f"  👁️ Monitoreando wallets {start+1}-{min(end, len(wallets))} de {len(wallets)}...")

                sw_tokens = []
                for wallet in wallets_batch:
                    try:
                        txs = get_wallet_transactions(wallet["address"], limit=5)
                        for tx in txs:
                            if tx.get("type") == "SWAP":
                                token_transfers = tx.get("tokenTransfers", [])
                                for transfer in token_transfers:
                                    mint = transfer.get("mint", "")
                                    if mint and mint not in sw_tokens:
                                        sw_tokens.append(mint)
                                        print(f"    🎯 {wallet['label']}: compró {mint[:12]}...")
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"    ⚠️ Error monitoreando {wallet['label']}: {e}")
            else:
                sw_tokens = []
                print("  ⚠️ No hay smart wallets")

            # Combinar tokens encontrados
            all_tokens = list(set(new_tokens + sw_tokens))

            # FASE 3: Analizar tokens prometedores
            if all_tokens:
                print(f"")
                print(f"📊 Analizando {len(all_tokens)} tokens...")

                for mint in all_tokens[:5]:
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
