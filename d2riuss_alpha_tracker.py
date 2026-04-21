import os
import sys
import json
import time
import random
import requests
from datetime import datetime, timedelta
from collections import defaultdict

# ============================================================
# D2RIUSS ALPHA TRACKER v2.0
# by @d2riuss
# Solana Smart Wallet Monitor + Token Analyzer + Telegram Bot
# ============================================================

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "ac619ff6-9d50-4a09-99ff-5a03c556302b")
HELIUS_RPC = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
HELIUS_API = f"https://api.helius.xyz/v0"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8648370563:AAEcv5kKvDOMUHcYRFb4IGVE5UicnZdWM88")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1454858664")

RAYDIUM_V4 = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
PUMP_FUN = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
JUPITER_V6 = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
WSOL = "So11111111111111111111111111111111111111111112"

STABLECOINS = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT",
}

SEED_TOKENS = {
    "HaP8r3ksG76PhQLTqR8FYBeNiQpejcFbQmiHbg787Ut5": "TRUMP",
    "Df6yfrKC8kZE3KNkrHERKzAetSxbrWeniQfyJY4Jpump": "CHILLGUY",
    "MEW1gQWJ3nEXg2qgERiKu7FAFj79PHvQVREQUzScPP5": "MEW",
    "ED5nyyWEzpPPiWimP8vYm7sD7TD3LAt3Q3gRTWHzPJBY": "MOODENG",
}

ELITE_WALLETS = {
    "DNfuF1L62WWyW3pNakVkyGGFzVVhj4Yr52jSmdTyeBHm": {"name": "Whale Alpha #1", "source": "seed", "wins": 5, "total": 6},
    "JBRBr3YgiLFR4zcaBXYsQwVMBMo4dQFNbSowtMAvFcYx": {"name": "Degen Sniper #1", "source": "seed", "wins": 4, "total": 5},
    "5YnSBi3Kpvtfm3gB9Dlz7gPNpMz4B3oFaLaLwDq5SUvs": {"name": "Smart Money #1", "source": "seed", "wins": 3, "total": 4},
    "7rhxnLV8C76MzQBL4hzGKMGBuf1uVMfBmoTwfRGji4xw": {"name": "Pump Hunter #1", "source": "seed", "wins": 4, "total": 5},
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM": {"name": "Early Bird #1", "source": "seed", "wins": 3, "total": 5},
    "3FqUrTgMBBg9tpYPMxBVRYBshtEBKH2jY3CRGXQ4Kx1Z": {"name": "Gem Finder #1", "source": "seed", "wins": 5, "total": 7},
    "HBSiKbz3pWRcLppkg3YRJQ5Fv3YxnDCLPETBFJcgXK9o": {"name": "Whale Alpha #2", "source": "seed", "wins": 4, "total": 6},
}

tracked_wallets = {}
discovered_tokens = {}
alerted_tokens = set()
wallet_scores = defaultdict(lambda: {"wins": 0, "total": 0})
scan_cycle = 0
bot_start_time = datetime.now()
command_offset = 0

# ============================================================
# TELEGRAM
# ============================================================

def tg_send(text, parse_mode="HTML"):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text[:4000], "parse_mode": parse_mode}
        r = requests.post(url, json=payload, timeout=10)
        return r.ok
    except Exception as e:
        print(f"[TG ERROR] {e}")
        return False

def tg_get_updates():
    global command_offset
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = {"offset": command_offset, "timeout": 1, "limit": 10}
        r = requests.get(url, params=params, timeout=5)
        if r.ok:
            data = r.json()
            if data.get("result"):
                for update in data["result"]:
                    command_offset = update["update_id"] + 1
                return data["result"]
    except Exception as e:
        print(f"[TG UPDATES ERROR] {e}")
    return []

# ============================================================
# HELIUS API
# ============================================================

def helius_rpc(method, params):
    try:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        r = requests.post(HELIUS_RPC, json=payload, timeout=15)
        if r.ok:
            return r.json().get("result")
    except Exception as e:
        print(f"[RPC ERROR] {method}: {e}")
    return None

def helius_api(endpoint, params=None):
    try:
        url = f"{HELIUS_API}/{endpoint}?api-key={HELIUS_API_KEY}"
        r = requests.get(url, params=params or {}, timeout=15)
        if r.ok:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] {endpoint}: {e}")
    return None

def get_signatures(wallet, limit=5):
    result = helius_rpc("getSignaturesForAddress", [wallet, {"limit": limit}])
    return result or []

def get_transaction(sig):
    try:
        url = f"{HELIUS_API}/transactions/?api-key={HELIUS_API_KEY}"
        r = requests.post(url, json={"transactions": [sig]}, timeout=15)
        if r.ok:
            data = r.json()
            if data and len(data) > 0:
                return data[0]
    except Exception as e:
        print(f"[TX ERROR] {e}")
    return None

def get_token_metadata(mint):
    try:
        url = f"{HELIUS_API}/token-metadata?api-key={HELIUS_API_KEY}"
        r = requests.post(url, json={"mintAccounts": [mint], "includeOffChain": True}, timeout=15)
        if r.ok:
            data = r.json()
            if data and len(data) > 0:
                return data[0]
    except Exception as e:
        print(f"[META ERROR] {e}")
    return None

def get_token_holders(mint):
    try:
        result = helius_rpc("getTokenLargestAccounts", [mint])
        if result and result.get("value"):
            return len(result["value"])
    except:
        pass
    return 0

def get_token_supply(mint):
    try:
        result = helius_rpc("getTokenSupply", [mint])
        if result and result.get("value"):
            return float(result["value"].get("uiAmount", 0))
    except:
        pass
    return 0

# ============================================================
# RUGCHECK
# ============================================================

def check_rugpull_risk(mint):
    try:
        url = f"https://api.rugcheck.xyz/v1/tokens/{mint}/report"
        r = requests.get(url, timeout=10)
        if r.ok:
            data = r.json()
            risks = data.get("risks", [])
            score = data.get("score", 0)
            top_holders = data.get("topHolders", [])
            lp_locked = False
            mint_disabled = False
            freeze_disabled = False
            for risk in risks:
                name = risk.get("name", "").lower()
                if "lp" in name and "lock" in name:
                    lp_locked = True
                if "mint" in name and ("disabled" in name or "revoked" in name):
                    mint_disabled = True
                if "freeze" in name and ("disabled" in name or "revoked" in name):
                    freeze_disabled = True
            top_holder_pct = 0
            if top_holders:
                for h in top_holders[:5]:
                    top_holder_pct += h.get("pct", 0)
            return {
                "score": score, "risks": risks, "lp_locked": lp_locked,
                "mint_disabled": mint_disabled, "freeze_disabled": freeze_disabled,
                "top5_holder_pct": round(top_holder_pct, 2), "risk_count": len(risks),
            }
    except Exception as e:
        print(f"[RUGCHECK ERROR] {e}")
    return None

# ============================================================
# TOKEN SCORING
# ============================================================

def score_token(mint, token_info=None):
    score = 50
    details = []
    rug = check_rugpull_risk(mint)
    if rug:
        if rug["mint_disabled"]:
            score += 10
            details.append("Mint revoked +10")
        else:
            score -= 15
            details.append("Mint active -15")
        if rug["freeze_disabled"]:
            score += 10
            details.append("Freeze revoked +10")
        else:
            score -= 10
            details.append("Freeze active -10")
        if rug["lp_locked"]:
            score += 15
            details.append("LP locked +15")
        else:
            score -= 10
            details.append("LP not locked -10")
        if rug["top5_holder_pct"] > 50:
            score -= 20
            details.append(f"Top5 hold {rug['top5_holder_pct']}% -20")
        elif rug["top5_holder_pct"] > 30:
            score -= 10
            details.append(f"Top5 hold {rug['top5_holder_pct']}% -10")
        else:
            score += 10
            details.append(f"Top5 hold {rug['top5_holder_pct']}% +10")
        if rug["risk_count"] > 5:
            score -= 15
            details.append(f"{rug['risk_count']} risks -15")
        elif rug["risk_count"] > 2:
            score -= 5
            details.append(f"{rug['risk_count']} risks -5")
    wallets_buying = 0
    for waddr, wdata in tracked_wallets.items():
        recent = wdata.get("recent_buys", [])
        for buy in recent:
            if buy.get("mint") == mint:
                wallets_buying += 1
                break
    if wallets_buying >= 3:
        score += 20
        details.append(f"{wallets_buying} wallets buying +20")
    elif wallets_buying >= 2:
        score += 10
        details.append(f"{wallets_buying} wallets buying +10")
    score = max(0, min(100, score))
    if score >= 75:
        rating = "STRONG BUY"
    elif score >= 55:
        rating = "MODERATE"
    elif score >= 35:
        rating = "RISKY"
    else:
        rating = "AVOID"
    return {"score": score, "rating": rating, "details": details, "rug": rug}

# ============================================================
# CONTRACT ANALYZER
# ============================================================

def analyze_contract(mint):
    meta = get_token_metadata(mint)
    supply = get_token_supply(mint)
    holders = get_token_holders(mint)
    scoring = score_token(mint)
    rug = scoring.get("rug")
    name = "Unknown"
    symbol = "???"
    if meta:
        on_chain = meta.get("onChainMetadata", {})
        off_chain = meta.get("offChainMetadata", {})
        if on_chain and on_chain.get("metadata"):
            md = on_chain["metadata"].get("data", {})
            name = md.get("name", name)
            symbol = md.get("symbol", symbol)
        if off_chain and off_chain.get("metadata"):
            name = off_chain["metadata"].get("name", name)
            symbol = off_chain["metadata"].get("symbol", symbol)
    lines = []
    lines.append("\U0001f50d <b>D2RIUSS Contract Analysis</b>")
    lines.append("\u2500" * 20)
    lines.append(f"<b>Token:</b> {name} (${symbol})")
    lines.append(f"<b>CA:</b> <code>{mint}</code>")
    lines.append(f"<b>Supply:</b> {supply:,.0f}")
    lines.append(f"<b>Holders:</b> ~{holders}+ (top accounts)")
    lines.append("")
    lines.append("\U0001f6e1 <b>Security Check:</b>")
    if rug:
        mint_s = "\u2705 Revoked" if rug["mint_disabled"] else "\u274c ACTIVE"
        freeze_s = "\u2705 Revoked" if rug["freeze_disabled"] else "\u274c ACTIVE"
        lp_s = "\u2705 Locked" if rug["lp_locked"] else "\u274c NOT LOCKED"
        lines.append(f"  Mint Authority: {mint_s}")
        lines.append(f"  Freeze Authority: {freeze_s}")
        lines.append(f"  LP: {lp_s}")
        lines.append(f"  Top 5 Holders: {rug['top5_holder_pct']}%")
        lines.append(f"  Risk Flags: {rug['risk_count']}")
    else:
        lines.append("  RugCheck data unavailable")
    lines.append("")
    lines.append(f"\U0001f4ca <b>D2RIUSS Score: {scoring['score']}/100</b>")
    lines.append(f"<b>Rating: {scoring['rating']}</b>")
    lines.append("")
    lines.append("<b>Breakdown:</b>")
    for d in scoring["details"]:
        lines.append(f"  \u2022 {d}")
    lines.append("")
    lines.append(f'\U0001f517 <a href="https://dexscreener.com/solana/{mint}">DexScreener</a> | <a href="https://rugcheck.xyz/tokens/{mint}">RugCheck</a> | <a href="https://solscan.io/token/{mint}">Solscan</a>')
    return "\n".join(lines)

# ============================================================
# WALLET DISCOVERY
# ============================================================

def discover_wallets_from_token(mint, token_name="Unknown"):
    print(f"[DISCOVER] Scanning {token_name} ({mint[:8]}...) for smart wallets")
    found = 0
    sigs = get_signatures(mint, limit=20)
    if not sigs:
        return found
    for sig_info in sigs:
        sig = sig_info.get("signature")
        if not sig:
            continue
        tx = get_transaction(sig)
        if not tx:
            continue
        tx_type = tx.get("type", "")
        if tx_type not in ["SWAP", "TRANSFER"]:
            continue
        fee_payer = tx.get("feePayer", "")
        if not fee_payer or fee_payer in tracked_wallets:
            continue
        if len(fee_payer) < 32:
            continue
        token_transfers = tx.get("tokenTransfers", [])
        for tt in token_transfers:
            if tt.get("mint") == mint:
                tracked_wallets[fee_payer] = {
                    "name": f"Discovered_{token_name}_{found+1}",
                    "source": token_name,
                    "discovered": datetime.now().isoformat(),
                    "recent_buys": [],
                    "tx_count": 0,
                }
                wallet_scores[fee_payer]["total"] += 1
                found += 1
                print(f"  [+] Found wallet: {fee_payer[:16]}...")
                if found >= 5:
                    return found
                break
        time.sleep(0.3)
    return found

def init_wallets():
    print("[INIT] Loading elite wallets...")
    for addr, info in ELITE_WALLETS.items():
        tracked_wallets[addr] = {
            "name": info["name"],
            "source": info["source"],
            "discovered": datetime.now().isoformat(),
            "recent_buys": [],
            "tx_count": 0,
        }
        wallet_scores[addr]["wins"] = info["wins"]
        wallet_scores[addr]["total"] = info["total"]
    print(f"[INIT] Loaded {len(ELITE_WALLETS)} elite wallets")
    seeds = list(SEED_TOKENS.items())
    random.shuffle(seeds)
    for mint, name in seeds[:2]:
        found = discover_wallets_from_token(mint, name)
        print(f"[INIT] Discovered {found} wallets from {name}")
        time.sleep(1)
    print(f"[INIT] Total wallets tracking: {len(tracked_wallets)}")

# ============================================================
# WALLET MONITORING
# ============================================================

def extract_token_info(meta):
    name = "Unknown"
    symbol = "???"
    if meta:
        on_chain = meta.get("onChainMetadata", {})
        off_chain = meta.get("offChainMetadata", {})
        if on_chain and on_chain.get("metadata"):
            md = on_chain["metadata"].get("data", {})
            name = md.get("name", name)
            symbol = md.get("symbol", symbol)
        if off_chain and off_chain.get("metadata"):
            name = off_chain["metadata"].get("name", name)
            symbol = off_chain["metadata"].get("symbol", symbol)
    return name, symbol

def check_wallet_activity(wallet_addr, wallet_info):
    alerts = []
    sigs = get_signatures(wallet_addr, limit=3)
    if not sigs:
        return alerts
    for sig_info in sigs:
        sig = sig_info.get("signature", "")
        if not sig or sig in alerted_tokens:
            continue
        tx = get_transaction(sig)
        if not tx:
            continue
        if tx.get("type", "") != "SWAP":
            continue
        token_transfers = tx.get("tokenTransfers", [])
        native_transfers = tx.get("nativeTransfers", [])
        sol_spent = 0
        token_received = None
        token_amount = 0
        for nt in native_transfers:
            if nt.get("fromUserAccount") == wallet_addr:
                sol_spent += nt.get("amount", 0) / 1e9
        for tt in token_transfers:
            m = tt.get("mint", "")
            if m == WSOL or m in STABLECOINS:
                continue
            if tt.get("toUserAccount") == wallet_addr:
                token_received = m
                token_amount = tt.get("tokenAmount", 0)
        if not token_received or sol_spent < 0.1:
            continue
        alerted_tokens.add(sig)
        wallet_info["recent_buys"].append({
            "mint": token_received, "sol_spent": sol_spent,
            "amount": token_amount, "time": datetime.now().isoformat(), "sig": sig,
        })
        wallet_info["tx_count"] = wallet_info.get("tx_count", 0) + 1
        meta = get_token_metadata(token_received)
        token_name, token_symbol = extract_token_info(meta)
        scoring = score_token(token_received)
        wname = wallet_info.get("name", wallet_addr[:12])
        ws = wallet_scores[wallet_addr]
        win_rate = (ws["wins"] / ws["total"] * 100) if ws["total"] > 0 else 0
        lines = []
        lines.append("\U0001f6a8 <b>D2RIUSS ALPHA ALERT</b> \U0001f6a8")
        lines.append("\u2500" * 20)
        lines.append(f"\U0001f4b0 <b>{token_name}</b> (${token_symbol})")
        lines.append(f"\U0001f4cb CA: <code>{token_received}</code>")
        lines.append("")
        lines.append(f"\U0001f46b <b>Wallet:</b> {wname}")
        lines.append(f"\U0001f4b5 <b>Spent:</b> {sol_spent:.2f} SOL")
        lines.append(f"\U0001f4c8 <b>Win Rate:</b> {win_rate:.0f}% ({ws['wins']}/{ws['total']})")
        lines.append("")
        lines.append(f"\U0001f4ca <b>D2RIUSS Score: {scoring['score']}/100</b>")
        lines.append(f"<b>Rating: {scoring['rating']}</b>")
        lines.append("")
        if scoring["details"]:
            lines.append("<b>Analysis:</b>")
            for d in scoring["details"]:
                lines.append(f"  \u2022 {d}")
            lines.append("")
        lines.append(f'<a href="https://dexscreener.com/solana/{token_received}">DexScreener</a> | <a href="https://rugcheck.xyz/tokens/{token_received}">RugCheck</a> | <a href="https://solscan.io/token/{token_received}">Solscan</a>')
        alerts.append("\n".join(lines))
        discovered_tokens[token_received] = {
            "name": token_name, "symbol": token_symbol,
            "discovered_by": wallet_addr, "wallet_name": wname,
            "sol_spent": sol_spent, "score": scoring["score"],
            "time": datetime.now().isoformat(),
        }
    return alerts

# ============================================================
# TELEGRAM COMMANDS
# ============================================================

def handle_commands():
    updates = tg_get_updates()
    for update in updates:
        msg_data = update.get("message", {})
        text = msg_data.get("text", "").strip()
        chat_id = str(msg_data.get("chat", {}).get("id", ""))
        if chat_id != TELEGRAM_CHAT_ID:
            continue
        if not text.startswith("/"):
            continue
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower().split("@")[0]
        arg = parts[1] if len(parts) > 1 else ""
        print(f"[CMD] {cmd} {arg[:20]}")
        if cmd == "/start" or cmd == "/help":
            cmd_help()
        elif cmd == "/analyze":
            cmd_analyze(arg)
        elif cmd == "/score":
            cmd_score(arg)
        elif cmd == "/wallets":
            cmd_wallets()
        elif cmd == "/addwallet":
            cmd_addwallet(arg)
        elif cmd == "/stats":
            cmd_stats()
        elif cmd == "/top":
            cmd_top()
        else:
            tg_send(f"\u2753 Unknown command: {cmd}\nUse /help to see available commands.")

def cmd_help():
    lines = []
    lines.append("\U0001f916 <b>D2RIUSS Alpha Tracker v2.0</b>")
    lines.append("\u2500" * 20)
    lines.append("")
    lines.append("<b>Commands:</b>")
    lines.append("/analyze CA - Full contract analysis")
    lines.append("/score CA - Quick safety score")
    lines.append("/wallets - List tracked wallets")
    lines.append("/addwallet ADDRESS NAME - Add wallet")
    lines.append("/top - Top discoveries today")
    lines.append("/stats - Bot statistics")
    lines.append("/help - This message")
    lines.append("")
    lines.append("\U0001f514 Auto-alerts when smart wallets buy new tokens")
    tg_send("\n".join(lines))

def cmd_analyze(ca):
    ca = ca.strip()
    if len(ca) < 32:
        tg_send("\u26a0\ufe0f Send a valid Solana contract address.\nUsage: /analyze <CA>")
        return
    tg_send(f"\U0001f50d Analyzing {ca[:8]}...{ca[-4:]}...")
    result = analyze_contract(ca)
    tg_send(result)

def cmd_score(ca):
    ca = ca.strip()
    if len(ca) < 32:
        tg_send("\u26a0\ufe0f Send a valid Solana contract address.\nUsage: /score <CA>")
        return
    scoring = score_token(ca)
    lines = []
    lines.append(f"\U0001f4ca <b>Quick Score: {scoring['score']}/100</b>")
    lines.append(f"<b>Rating: {scoring['rating']}</b>")
    lines.append("")
    for d in scoring["details"]:
        lines.append(f"  \u2022 {d}")
    lines.append("")
    lines.append(f"<code>{ca}</code>")
    tg_send("\n".join(lines))

def cmd_wallets():
    lines = []
    lines.append(f"\U0001f46b <b>Tracked Wallets ({len(tracked_wallets)})</b>")
    lines.append("\u2500" * 20)
    lines.append("")
    sorted_w = sorted(tracked_wallets.items(), key=lambda x: wallet_scores[x[0]]["wins"], reverse=True)
    for i, (addr, info) in enumerate(sorted_w[:15]):
        ws = wallet_scores[addr]
        wr = (ws["wins"] / ws["total"] * 100) if ws["total"] > 0 else 0
        lines.append(f"{i+1}. <b>{info['name']}</b>")
        lines.append(f"   {addr[:8]}...{addr[-4:]} | WR: {wr:.0f}%")
    if len(tracked_wallets) > 15:
        lines.append(f"\n... and {len(tracked_wallets) - 15} more")
    tg_send("\n".join(lines))

def cmd_addwallet(arg):
    parts = arg.strip().split(maxsplit=1)
    if len(parts) < 1 or len(parts[0]) < 32:
        tg_send("\u26a0\ufe0f Usage: /addwallet ADDRESS NAME\nExample: /addwallet ABC123... My Whale")
        return
    addr = parts[0]
    name = parts[1] if len(parts) > 1 else f"Custom_{len(tracked_wallets)+1}"
    if addr in tracked_wallets:
        tg_send(f"\u26a0\ufe0f Wallet already tracked as: {tracked_wallets[addr]['name']}")
        return
    tracked_wallets[addr] = {
        "name": name, "source": "manual",
        "discovered": datetime.now().isoformat(),
        "recent_buys": [], "tx_count": 0,
    }
    wallet_scores[addr] = {"wins": 0, "total": 0}
    tg_send(f"\u2705 Added wallet: <b>{name}</b>\n<code>{addr}</code>")

def cmd_stats():
    uptime = datetime.now() - bot_start_time
    hours = uptime.total_seconds() / 3600
    lines = []
    lines.append("\U0001f4ca <b>D2RIUSS Alpha Tracker Stats</b>")
    lines.append("\u2500" * 20)
    lines.append("")
    lines.append(f"\u23f1 <b>Uptime:</b> {hours:.1f}h")
    lines.append(f"\U0001f504 <b>Scan Cycles:</b> {scan_cycle}")
    lines.append(f"\U0001f46b <b>Wallets Tracked:</b> {len(tracked_wallets)}")
    lines.append(f"\U0001f48e <b>Tokens Discovered:</b> {len(discovered_tokens)}")
    lines.append(f"\U0001f6a8 <b>Alerts Sent:</b> {len(alerted_tokens)}")
    lines.append("")
    lines.append("<b>Version:</b> 2.0")
    tg_send("\n".join(lines))

def cmd_top():
    if not discovered_tokens:
        tg_send("\U0001f4ed No tokens discovered yet. Monitoring...")
        return
    sorted_t = sorted(discovered_tokens.items(), key=lambda x: x[1].get("score", 0), reverse=True)
    lines = []
    lines.append("\U0001f3c6 <b>Top Discoveries</b>")
    lines.append("\u2500" * 20)
    lines.append("")
    for i, (mint, info) in enumerate(sorted_t[:10]):
        lines.append(f"{i+1}. <b>{info['name']}</b> (${info['symbol']})")
        lines.append(f"   Score: {info['score']}/100 | {info['sol_spent']:.1f} SOL")
        lines.append(f"   By: {info['wallet_name']}")
        lines.append("")
    tg_send("\n".join(lines))

# ============================================================
# MAIN LOOP
# ============================================================

def main():
    global scan_cycle
    print("=" * 50)
    print("D2RIUSS ALPHA TRACKER v2.0")
    print("=" * 50)
    init_wallets()
    lines = []
    lines.append("\U0001f7e2 <b>D2RIUSS Alpha Tracker v2.0 ONLINE</b>")
    lines.append("")
    lines.append(f"\U0001f46b Tracking {len(tracked_wallets)} wallets")
    lines.append("\U0001f50d Smart wallet monitoring active")
    lines.append("\U0001f4ca Token scoring engine ready")
    lines.append("\U0001f916 Command system active")
    lines.append("")
    lines.append("Type /help for commands")
    tg_send("\n".join(lines))
    print(f"[READY] Monitoring {len(tracked_wallets)} wallets")
    print("[READY] Command system active")
    while True:
        try:
            scan_cycle += 1
            handle_commands()
            wallet_list = list(tracked_wallets.items())
            if not wallet_list:
                print(f"[CYCLE {scan_cycle}] No wallets to monitor")
                time.sleep(30)
                continue
            wallets_per_cycle = min(5, len(wallet_list))
            start_idx = (scan_cycle * wallets_per_cycle) % len(wallet_list)
            for i in range(wallets_per_cycle):
                idx = (start_idx + i) % len(wallet_list)
                addr, info = wallet_list[idx]
                alerts = check_wallet_activity(addr, info)
                for alert in alerts:
                    tg_send(alert)
                    time.sleep(1)
                time.sleep(0.5)
            if scan_cycle % 100 == 0:
                status = f"\U0001f504 <b>Cycle {scan_cycle}</b> | "
                status += f"\U0001f46b {len(tracked_wallets)} wallets | "
                status += f"\U0001f48e {len(discovered_tokens)} tokens | "
                status += f"\U0001f6a8 {len(alerted_tokens)} alerts"
                tg_send(status)
                print(f"[STATUS] Cycle {scan_cycle} | {len(tracked_wallets)} wallets | {len(discovered_tokens)} tokens")
            if scan_cycle % 200 == 0 and discovered_tokens:
                recent = sorted(discovered_tokens.items(), key=lambda x: x[1].get("score", 0), reverse=True)
                if recent:
                    best_mint = recent[0][0]
                    best_name = recent[0][1].get("name", "Unknown")
                    found = discover_wallets_from_token(best_mint, best_name)
                    if found > 0:
                        tg_send(f"\U0001f50d Discovered {found} new wallets from {best_name}")
            time.sleep(15)
        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Stopping D2RIUSS Alpha Tracker...")
            tg_send("\U0001f534 D2RIUSS Alpha Tracker v2.0 shutting down...")
            break
        except Exception as e:
            print(f"[ERROR] Cycle {scan_cycle}: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
