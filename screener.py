"""
Core stock screening engine — yfinance 1.x compatible.
PRO upgrades:
- Volume + OBV confirmation on oversold signal
- MACD histogram turn-up = early reversal trigger
- Liquidity floor ($5M+ avg daily $-volume)
- Earnings blackout (±5 days) — auto-downgrades to WATCH
- Piotroski F-Score (read from quality cache)
- FCF yield (read from quality cache)
- Multi-day persistence (🔥 if appeared in top 10 ≥2 of last 3 days)
- Market regime banner (SPY/HSI/STI vs 200MA + VIX)
- Sector cap (max 3 per sector for correlation control)
- Trade plan per pick: entry / ATR-based stop / 2% target / R:R / suggested shares
"""

import json
import time
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf
import pytz
import requests

from stocks import MARKET_CONFIG, COMPANY_NAMES

logger = logging.getLogger(__name__)

# ── Pipeline constants ────────────────────────────────────────────────────────
BATCH_SIZE = 25
BATCH_DELAY = 2.5
INFO_DELAY = 1.5
MAX_INFO_CALLS = 40
INFO_RETRIES = 3

# ── Pro screener thresholds ───────────────────────────────────────────────────
DOLLAR_VOL_MIN_USD = 5_000_000          # min 20-day avg $-volume
ATR_STOP_MULT = 1.2                     # stop = entry − 1.2 × ATR (tuned for daily swing)
TARGET_PCT = 2.5                        # target = +2.5% (middle of user's 1-3% band)
MIN_RR = 1.0                            # minimum reward:risk for SWING BUY (mean-reversion is win-rate-driven, not R:R-driven)
SECTOR_CAP = 3                          # max picks per sector in final top 10
PORTFOLIO_USD = 100_000                 # template portfolio for sizing
PORTFOLIO_RISK_PCT = 1.0                # risk 1% per trade
EARNINGS_BLACKOUT_DAYS = 5              # ±5 trading days around earnings

# ── Cache files ───────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
FUNDAMENTALS_CACHE_FILE = DATA_DIR / "fundamentals_cache.json"
QUALITY_CACHE_FILE = DATA_DIR / "quality_cache.json"

# ── Regime tickers per market ─────────────────────────────────────────────────
REGIME_TICKERS = {
    "US": {"index": "SPY",       "vix": "^VIX"},
    "HK": {"index": "2800.HK",   "vix": "^VHSI"},
    "SG": {"index": "ES3.SI",    "vix": None},
}


def _load_json_cache(path: Path) -> dict:
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


_FUND_CACHE: dict = _load_json_cache(FUNDAMENTALS_CACHE_FILE)
_QUALITY_CACHE: dict = _load_json_cache(QUALITY_CACHE_FILE)
logger.info(f"Caches loaded: fundamentals={len(_FUND_CACHE)} quality={len(_QUALITY_CACHE)}")

_REGIME_CACHE: dict = {}  # per-report-run cache


# ══════════════════════════════════════════════════════════════════════════════
# Technical indicators
# ══════════════════════════════════════════════════════════════════════════════

def calc_rsi(prices: pd.Series, period: int = 14) -> float:
    delta = prices.diff().dropna()
    if len(delta) < period + 1:
        return float("nan")
    gain = delta.clip(lower=0).ewm(com=period - 1, min_periods=period).mean()
    loss = (-delta.clip(upper=0)).ewm(com=period - 1, min_periods=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 1)


def calc_atr_pct(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    if pd.isna(atr) or close.iloc[-1] == 0:
        return float("nan")
    return round(float(atr / close.iloc[-1] * 100), 2)


def pct_of_range(val: float, low: float, high: float) -> float:
    if high <= low:
        return 50.0
    return round((val - low) / (high - low) * 100, 1)


def calc_macd_hist(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """MACD histogram — looks for early-reversal trigger (turning up while still negative)."""
    if len(close) < slow + signal + 1:
        return {"hist_now": None, "hist_prev": None, "turning_up": False}
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - sig
    hist_now = float(hist.iloc[-1])
    hist_prev = float(hist.iloc[-2])
    # Classic early-reversal: histogram still below zero but rising = bears losing steam
    turning_up = hist_now > hist_prev and hist_now < 0
    return {
        "hist_now": round(hist_now, 4),
        "hist_prev": round(hist_prev, 4),
        "turning_up": bool(turning_up),
    }


def calc_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume — institutional accumulation proxy."""
    direction = np.sign(close.diff().fillna(0))
    return (direction * volume).cumsum()


def volume_signal(close: pd.Series, volume: pd.Series) -> dict:
    """
    Volume confirmation for the oversold signal:
      - vol_ratio: today's volume / 20-day average
      - obv_slope: % change in OBV over last 10 days
      - confirmed: vol > 1.1x avg AND OBV rising
    """
    if len(close) < 20 or len(volume) < 20:
        return {"vol_ratio": None, "obv_slope": None, "confirmed": False}
    avg20 = float(volume.tail(20).mean())
    vt = float(volume.iloc[-1])
    vol_ratio = round(vt / avg20, 2) if avg20 > 0 else None

    obv = calc_obv(close, volume)
    obv_slope = None
    if len(obv) >= 11:
        obv_10ago = float(obv.iloc[-11])
        obv_now = float(obv.iloc[-1])
        if abs(obv_10ago) > 0:
            obv_slope = round((obv_now - obv_10ago) / abs(obv_10ago) * 100, 1)

    confirmed = bool(
        (vol_ratio is not None and vol_ratio > 1.1)
        and (obv_slope is not None and obv_slope > 0)
    )
    return {"vol_ratio": vol_ratio, "obv_slope": obv_slope, "confirmed": confirmed}


def avg_dollar_volume(close: pd.Series, volume: pd.Series, period: int = 20) -> Optional[float]:
    if len(close) < period or len(volume) < period:
        return None
    dv = (close.tail(period) * volume.tail(period)).mean()
    return float(dv) if not pd.isna(dv) else None


# ══════════════════════════════════════════════════════════════════════════════
# Market regime
# ══════════════════════════════════════════════════════════════════════════════

def get_market_regime(market_code: str) -> dict:
    """Risk-on / risk-off classification based on index vs 200MA and VIX level."""
    if market_code in _REGIME_CACHE:
        return _REGIME_CACHE[market_code]

    tickers = REGIME_TICKERS.get(market_code, {})
    idx_ticker = tickers.get("index")
    vix_ticker = tickers.get("vix")

    result = {
        "label": "neutral",
        "index_ticker": idx_ticker,
        "index_above_200ma": None,
        "index_pct_vs_ma200": None,
        "vix_ticker": vix_ticker,
        "vix_level": None,
        "note": "",
    }

    try:
        idx_df = yf.download(idx_ticker, period="14mo", interval="1d",
                             auto_adjust=True, progress=False, group_by="column")
        if not idx_df.empty:
            if isinstance(idx_df.columns, pd.MultiIndex):
                close = idx_df[("Close", idx_ticker)] if ("Close", idx_ticker) in idx_df.columns else idx_df["Close"].iloc[:, 0]
            else:
                close = idx_df["Close"]
            close = close.dropna()
            if len(close) >= 200:
                ma200 = float(close.rolling(200).mean().iloc[-1])
                current = float(close.iloc[-1])
                result["index_above_200ma"] = current > ma200
                result["index_pct_vs_ma200"] = round((current - ma200) / ma200 * 100, 1)
    except Exception as e:
        logger.warning(f"Regime index fetch failed for {idx_ticker}: {e}")

    if vix_ticker:
        try:
            vix_df = yf.download(vix_ticker, period="3mo", interval="1d",
                                 auto_adjust=True, progress=False, group_by="column")
            if not vix_df.empty:
                if isinstance(vix_df.columns, pd.MultiIndex):
                    c = vix_df[("Close", vix_ticker)] if ("Close", vix_ticker) in vix_df.columns else vix_df["Close"].iloc[:, 0]
                else:
                    c = vix_df["Close"]
                c = c.dropna()
                if len(c):
                    result["vix_level"] = round(float(c.iloc[-1]), 1)
        except Exception as e:
            logger.warning(f"VIX fetch failed for {vix_ticker}: {e}")

    above = result["index_above_200ma"]
    vix = result["vix_level"]
    if above is True and (vix is None or vix < 22):
        result["label"] = "risk_on"
        result["note"] = "Index above 200-day MA, volatility contained — favourable for mean-reversion longs."
    elif above is False or (vix is not None and vix > 28):
        result["label"] = "risk_off"
        result["note"] = "Index below 200-day MA or elevated VIX — tighten stops, expect fewer clean signals."
    else:
        result["label"] = "neutral"
        result["note"] = "Mixed regime — selective entries, prioritise high-confidence picks only."

    _REGIME_CACHE[market_code] = result
    return result


# ══════════════════════════════════════════════════════════════════════════════
# Multi-day persistence
# ══════════════════════════════════════════════════════════════════════════════

def get_persistence_count(ticker: str, market: str, depth: int = 3) -> int:
    """Count how many of the last `depth` daily reports had this ticker in top 10."""
    if not DATA_DIR.exists():
        return 0
    today = date.today().isoformat()
    archives = sorted(
        [p for p in DATA_DIR.glob("report_*.json") if today not in p.name],
        reverse=True,
    )[:depth]
    count = 0
    for arch in archives:
        try:
            r = json.loads(arch.read_text())
            picks = r.get("markets", {}).get(market, {}).get("picks", [])
            if any(p.get("ticker") == ticker for p in picks):
                count += 1
        except Exception:
            continue
    return count


# ══════════════════════════════════════════════════════════════════════════════
# Trade plan
# ══════════════════════════════════════════════════════════════════════════════

def build_trade_plan(price: float, atr_pct: float, currency: str) -> dict:
    """Compute entry / stop / target / R:R / suggested position size."""
    if not price or pd.isna(price) or not atr_pct or pd.isna(atr_pct):
        return {}
    atr_dollar = price * atr_pct / 100
    stop_dist = atr_dollar * ATR_STOP_MULT
    stop = round(price - stop_dist, 4)
    target = round(price * (1 + TARGET_PCT / 100), 4)
    target_dist = target - price
    rr = round(target_dist / stop_dist, 2) if stop_dist > 0 else 0.0

    fx_to_usd = {"HKD": 7.8, "SGD": 1.35}.get(currency, 1.0)
    stop_dist_usd = stop_dist / fx_to_usd
    risk_budget_usd = PORTFOLIO_USD * PORTFOLIO_RISK_PCT / 100  # $1,000 default
    shares = int(risk_budget_usd / stop_dist_usd) if stop_dist_usd > 0 else 0

    return {
        "entry": round(price, 4),
        "stop": stop,
        "target": target,
        "rr": rr,
        "stop_pct": round(stop_dist / price * 100, 2),
        "target_pct": round(target_dist / price * 100, 2),
        "suggested_shares": shares,
        "risk_per_trade_usd": int(risk_budget_usd),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Earnings blackout
# ══════════════════════════════════════════════════════════════════════════════

def is_earnings_blackout(earnings_date_str: Optional[str], blackout_days: int = EARNINGS_BLACKOUT_DAYS) -> bool:
    if not earnings_date_str:
        return False
    try:
        ed = datetime.strptime(earnings_date_str[:10], "%Y-%m-%d").date()
        return abs((ed - date.today()).days) <= blackout_days
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# Scoring (extended)
# ══════════════════════════════════════════════════════════════════════════════

def score_stock(m: dict, regime: dict) -> float:
    score = 0.0

    rsi = m.get("rsi")
    if rsi and not pd.isna(rsi):
        if 28 <= rsi <= 42:       score += 22
        elif 20 <= rsi < 28:      score += 13
        elif 42 < rsi <= 52:      score += 10

    pos52 = m.get("pos_52w")
    if pos52 is not None and not pd.isna(pos52):
        if pos52 <= 20:           score += 17
        elif pos52 <= 35:         score += 14
        elif pos52 <= 50:         score += 9
        elif pos52 <= 65:         score += 3

    vs_ma50 = m.get("vs_ma50_pct")
    if vs_ma50 is not None and not pd.isna(vs_ma50):
        if -15 <= vs_ma50 <= -2:  score += 14
        elif -2 < vs_ma50 <= 2:   score += 6
        elif vs_ma50 < -15:       score += 4

    pe = m.get("pe")
    if pe and not pd.isna(pe):
        if 0 < pe <= 12:          score += 13
        elif 12 < pe <= 18:       score += 9
        elif 18 < pe <= 25:       score += 4

    pb = m.get("pb")
    if pb and not pd.isna(pb):
        if 0 < pb <= 1.5:         score += 10
        elif 1.5 < pb <= 2.5:     score += 6
        elif 2.5 < pb <= 3.5:     score += 3

    atr = m.get("atr_pct")
    if atr and not pd.isna(atr):
        if atr >= 3.0:            score += 8
        elif atr >= 2.0:          score += 6
        elif atr >= 1.5:          score += 4

    # ── NEW: Volume confirmation ──────────────────────────────────────────────
    vol = m.get("volume_signal") or {}
    if vol.get("confirmed"):
        score += 10
    elif vol.get("vol_ratio") and vol["vol_ratio"] > 1.0:
        score += 4

    # ── NEW: MACD turn-up (early reversal) ────────────────────────────────────
    if (m.get("macd") or {}).get("turning_up"):
        score += 8

    # ── NEW: Piotroski F-Score (quality moat) ─────────────────────────────────
    fs = m.get("f_score")
    if fs is not None:
        if fs >= 7:               score += 8
        elif fs >= 5:              score += 4

    # ── NEW: FCF yield (genuinely cheap) ──────────────────────────────────────
    fcfy = m.get("fcf_yield")
    if fcfy is not None:
        if fcfy >= 7:              score += 6
        elif fcfy >= 5:            score += 4
        elif fcfy >= 3:            score += 2

    # ── NEW: Multi-day persistence ────────────────────────────────────────────
    pc = m.get("persistence_count", 0) or 0
    if pc >= 2:                    score += 6
    elif pc >= 1:                  score += 2

    # ── NEW: Regime adjustment ────────────────────────────────────────────────
    label = (regime or {}).get("label")
    if label == "risk_off":        score -= 12
    elif label == "risk_on":       score += 3

    # ── NEW: Earnings blackout penalty (severe) ───────────────────────────────
    if m.get("earnings_blackout"):
        score -= 30

    return round(max(0.0, score), 1)


def generate_rationale(m: dict) -> str:
    parts = []
    rsi = m.get("rsi")
    if rsi and not pd.isna(rsi):
        if rsi < 35:      parts.append(f"RSI {rsi:.0f} deeply oversold")
        elif rsi < 50:    parts.append(f"RSI {rsi:.0f} oversold")

    vol = m.get("volume_signal") or {}
    if vol.get("confirmed"):
        parts.append(f"vol {vol.get('vol_ratio')}x avg + OBV↑")

    if (m.get("macd") or {}).get("turning_up"):
        parts.append("MACD turning up")

    pos52 = m.get("pos_52w")
    if pos52 is not None and not pd.isna(pos52) and pos52 <= 35:
        parts.append(f"{pos52:.0f}% of 52W range")

    vs_ma = m.get("vs_ma50_pct")
    if vs_ma is not None and not pd.isna(vs_ma) and vs_ma <= -3:
        parts.append(f"{abs(vs_ma):.1f}% below 50d MA")

    pe = m.get("pe")
    if pe and 0 < pe < 18: parts.append(f"P/E {pe:.1f}")

    fs = m.get("f_score")
    if fs is not None and fs >= 7: parts.append(f"F-Score {fs}/9")

    fcfy = m.get("fcf_yield")
    if fcfy is not None and fcfy >= 5: parts.append(f"FCF yld {fcfy:.1f}%")

    pc = m.get("persistence_count", 0) or 0
    if pc >= 2: parts.append(f"🔥 {pc}d streak")

    if m.get("earnings_blackout"):
        ed = m.get("next_earnings", "")[:10]
        parts.append(f"⚠️ earnings {ed}")

    return " · ".join(parts) if parts else "Multi-factor value + momentum setup"


# ══════════════════════════════════════════════════════════════════════════════
# Data fetching
# ══════════════════════════════════════════════════════════════════════════════

def _safe(val, default=None):
    try:
        f = float(val)
        return None if (pd.isna(f) or np.isinf(f)) else f
    except Exception:
        return default


def fetch_batch_prices(tickers: list, period: str = "14mo") -> dict:
    """yfinance 1.x batched download (group_by='column' → MultiIndex (field, ticker))."""
    results = {}
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i: i + BATCH_SIZE]
        try:
            raw = yf.download(
                batch, period=period, interval="1d",
                auto_adjust=True, progress=False, group_by="column",
            )
            if raw.empty:
                continue
            for ticker in batch:
                try:
                    if len(batch) == 1:
                        df = raw.copy()
                        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
                    else:
                        df = pd.DataFrame({
                            field: raw[field][ticker]
                            for field in ["Open", "High", "Low", "Close", "Volume"]
                            if (field, ticker) in raw.columns or field in raw.columns.get_level_values(0)
                        })
                    df = df.dropna(subset=["Close"])
                    if len(df) >= 20:
                        results[ticker] = df
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Batch download failed for {batch[:3]}…: {e}")
        if i + BATCH_SIZE < len(tickers):
            time.sleep(BATCH_DELAY)
    return results


def fetch_fast_info(ticker: str) -> dict:
    try:
        fi = yf.Ticker(ticker).fast_info
        return {
            "market_cap": _safe(fi.market_cap),
            "year_high": _safe(fi.year_high),
            "year_low": _safe(fi.year_low),
            "fifty_day_average": _safe(fi.fifty_day_average),
            "last_price": _safe(fi.last_price),
            "previous_close": _safe(fi.regular_market_previous_close),
        }
    except Exception:
        return {}


_YF_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://finance.yahoo.com",
}

def fetch_fundamentals(ticker: str) -> dict:
    """Priority: committed cache → live Yahoo v8 → yfinance .info."""
    base_name = COMPANY_NAMES.get(ticker, "")
    cached = _FUND_CACHE.get(ticker, {})
    base = {
        "name": base_name or ticker,
        "sector": cached.get("sector", ""),
        "pe": _safe(cached.get("pe")) if cached.get("pe") else None,
        "pb": _safe(cached.get("pb")) if cached.get("pb") else None,
        "roe": None,
    }
    if base["pe"] or base["pb"]:
        return base

    for attempt in range(INFO_RETRIES):
        try:
            url = (
                f"https://query1.finance.yahoo.com/v8/finance/quoteSummary/{ticker}"
                f"?modules=defaultKeyStatistics,summaryDetail,assetProfile"
            )
            r = requests.get(url, headers=_YF_HEADERS, timeout=12)
            if r.status_code == 429:
                time.sleep(3 * (attempt + 1)); continue
            r.raise_for_status()
            body = r.json().get("quoteSummary", {}).get("result", [])
            if not body:
                raise ValueError("Empty result")
            d = body[0]
            ks = d.get("defaultKeyStatistics", {})
            sd = d.get("summaryDetail", {})
            ap = d.get("assetProfile", {})
            pe = _safe(sd.get("trailingPE", {}).get("raw") or ks.get("forwardPE", {}).get("raw"))
            pb = _safe(ks.get("priceToBook", {}).get("raw"))
            return {
                "name": base_name or ticker,
                "sector": ap.get("sector", base["sector"]),
                "pe": pe, "pb": pb, "roe": None,
            }
        except Exception:
            if attempt < INFO_RETRIES - 1:
                time.sleep(2 * (attempt + 1))

    try:
        info = yf.Ticker(ticker).info
        if info:
            pe_raw = info.get("trailingPE") or info.get("forwardPE")
            return {
                "name": base_name or info.get("longName") or ticker,
                "sector": info.get("sector", base["sector"]),
                "pe": _safe(pe_raw),
                "pb": _safe(info.get("priceToBook")),
                "roe": None,
            }
    except Exception:
        pass

    return base


# ══════════════════════════════════════════════════════════════════════════════
# Sector cap (correlation control)
# ══════════════════════════════════════════════════════════════════════════════

def apply_sector_cap(picks: list, max_per_sector: int = SECTOR_CAP) -> list:
    """Limit final top-N to at most N per sector. Overflow appended at end so list isn't truncated."""
    seen, capped, overflow = {}, [], []
    for p in picks:
        sec = (p.get("sector") or "Unknown").strip() or "Unknown"
        if seen.get(sec, 0) < max_per_sector:
            capped.append(p)
            seen[sec] = seen.get(sec, 0) + 1
        else:
            overflow.append(p)
    return capped + overflow


# ══════════════════════════════════════════════════════════════════════════════
# Main screener
# ══════════════════════════════════════════════════════════════════════════════

def screen_market(market: str, top_n: int = 10) -> dict:
    config = MARKET_CONFIG[market]
    tickers = config["tickers"]
    currency = config["currency"]

    logger.info(f"[{market}] Fetching regime…")
    regime = get_market_regime(market)
    logger.info(f"[{market}] Regime: {regime.get('label')}")

    logger.info(f"[{market}] Fetching price data for {len(tickers)} tickers…")
    price_data = fetch_batch_prices(tickers)
    logger.info(f"[{market}] Got price data for {len(price_data)} tickers")

    fx_to_usd = {"HKD": 7.8, "SGD": 1.35}.get(currency, 1.0)
    dollar_vol_min_local = DOLLAR_VOL_MIN_USD * fx_to_usd

    candidates = []
    for ticker, df in price_data.items():
        try:
            close = df["Close"].dropna()
            if len(close) < 30:
                continue
            high = df["High"].dropna()
            low = df["Low"].dropna()
            volume = df["Volume"].dropna() if "Volume" in df.columns else pd.Series(dtype=float)

            current_price = float(close.iloc[-1])
            prev_close = float(close.iloc[-2]) if len(close) >= 2 else current_price
            day_change_pct = round((current_price - prev_close) / prev_close * 100, 2) if prev_close else 0

            rsi = calc_rsi(close)
            atr_pct = calc_atr_pct(high, low, close)

            ma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
            vs_ma50 = round((current_price - ma50) / ma50 * 100, 2) if ma50 and ma50 > 0 else None

            low52 = float(low.tail(252).min()) if len(low) >= 20 else float(low.min())
            high52 = float(high.tail(252).max()) if len(high) >= 20 else float(high.max())
            pos52 = pct_of_range(current_price, low52, high52)

            macd_info = calc_macd_hist(close)
            vol_info = volume_signal(close, volume) if len(volume) else {"vol_ratio": None, "obv_slope": None, "confirmed": False}
            dollar_vol = avg_dollar_volume(close, volume) if len(volume) else None

            # Liquidity floor — exclude illiquid names regardless of cap
            if dollar_vol is not None and dollar_vol < dollar_vol_min_local:
                continue

            persistence = get_persistence_count(ticker, market)

            candidates.append({
                "ticker": ticker,
                "name": COMPANY_NAMES.get(ticker, ""),
                "price": current_price,
                "day_change_pct": day_change_pct,
                "rsi": rsi,
                "atr_pct": atr_pct,
                "vs_ma50_pct": vs_ma50,
                "pos_52w": pos52,
                "low_52w": round(low52, 4),
                "high_52w": round(high52, 4),
                "currency": currency,
                "macd": macd_info,
                "volume_signal": vol_info,
                "avg_dollar_volume": dollar_vol,
                "persistence_count": persistence,
            })
        except Exception as e:
            logger.warning(f"[{market}] Error processing {ticker}: {e}")
            continue

    if not candidates:
        return {"picks": [], "regime": regime}

    # Pre-filter: RSI < 58 and not extended above 65% of 52W range
    candidates = [c for c in candidates if
                  (pd.isna(c["rsi"]) or c["rsi"] < 58) and c["pos_52w"] < 65]

    candidates.sort(key=lambda x: (x.get("pos_52w") or 100, x.get("rsi") or 100))
    top_pool = candidates[:MAX_INFO_CALLS]

    logger.info(f"[{market}] Enriching {len(top_pool)} candidates…")
    enriched = []
    for i, c in enumerate(top_pool):
        fi = fetch_fast_info(c["ticker"])
        mc = fi.get("market_cap")
        if mc:
            mc_usd = mc / 7.8 if currency == "HKD" else mc / 1.35 if currency == "SGD" else mc
            if mc_usd < 800_000_000:
                continue
        c["market_cap_raw"] = mc
        c.update(fi)
        enriched.append(c)
        if i % 5 == 4:
            time.sleep(0.5)

    # Top 25: full fundamentals + quality + score
    for i, c in enumerate(enriched[:25]):
        fund = fetch_fundamentals(c["ticker"])
        c.update(fund)
        if c.get("pe") and c["pe"] < 0:
            c["_skip"] = True
            continue

        q = _QUALITY_CACHE.get(c["ticker"], {})
        c["f_score"] = q.get("f_score")
        c["fcf_yield"] = q.get("fcf_yield")
        c["next_earnings"] = q.get("next_earnings")
        c["earnings_blackout"] = is_earnings_blackout(c.get("next_earnings"))

        c["score"] = score_stock(c, regime)
        c["rationale"] = generate_rationale(c)
        c["trade_plan"] = build_trade_plan(c["price"], c.get("atr_pct"), currency)
        time.sleep(INFO_DELAY)

    # Remaining: skip live fundamentals (rate-limit friendly), still score
    for c in enriched[25:]:
        c.setdefault("name", COMPANY_NAMES.get(c["ticker"], "") or c["ticker"])
        c.setdefault("sector", "")
        q = _QUALITY_CACHE.get(c["ticker"], {})
        c["f_score"] = q.get("f_score")
        c["fcf_yield"] = q.get("fcf_yield")
        c["next_earnings"] = q.get("next_earnings")
        c["earnings_blackout"] = is_earnings_blackout(c.get("next_earnings"))
        c["score"] = score_stock(c, regime)
        c["rationale"] = generate_rationale(c)
        c["trade_plan"] = build_trade_plan(c["price"], c.get("atr_pct"), currency)

    final = [c for c in enriched if not c.get("_skip")]
    final.sort(key=lambda x: x["score"], reverse=True)

    # Sector diversification cap (correlation control)
    final = apply_sector_cap(final, max_per_sector=SECTOR_CAP)

    results = []
    for rank, c in enumerate(final[:top_n], 1):
        mc = c.get("market_cap_raw")
        if mc:
            if mc >= 1e12:    mc_display = f"{mc/1e12:.1f}T"
            elif mc >= 1e9:   mc_display = f"{mc/1e9:.1f}B"
            else:             mc_display = f"{mc/1e6:.0f}M"
        else:                 mc_display = "—"

        tp = c.get("trade_plan", {}) or {}
        score = c["score"]
        rr = tp.get("rr", 0) or 0
        blackout = c.get("earnings_blackout", False)

        if blackout:
            signal = "AVOID"
        elif score >= 55 and rr >= MIN_RR:
            signal = "SWING BUY"
        elif score >= 35:
            signal = "WATCH"
        else:
            signal = "AVOID"

        results.append({
            "rank": rank,
            "ticker": c["ticker"],
            "name": c.get("name", c["ticker"]),
            "sector": c.get("sector", ""),
            "price": round(c["price"], 4),
            "currency": currency,
            "day_change_pct": c["day_change_pct"],
            "market_cap": mc_display,
            "pe": round(c["pe"], 1) if c.get("pe") else "—",
            "pb": round(c["pb"], 2) if c.get("pb") else "—",
            "rsi": c.get("rsi", "—"),
            "atr_pct": c.get("atr_pct", "—"),
            "pos_52w": c.get("pos_52w", "—"),
            "vs_ma50_pct": c.get("vs_ma50_pct", "—"),
            "low_52w": c.get("low_52w"),
            "high_52w": c.get("high_52w"),
            "score": score,
            "rationale": c["rationale"],
            "signal": signal,
            # NEW pro fields ↓
            "volume_signal": c.get("volume_signal") or {},
            "macd_turning_up": (c.get("macd") or {}).get("turning_up", False),
            "f_score": c.get("f_score"),
            "fcf_yield": c.get("fcf_yield"),
            "persistence_count": c.get("persistence_count", 0),
            "next_earnings": c.get("next_earnings"),
            "earnings_blackout": blackout,
            "trade_plan": tp,
        })

    return {"picks": results, "regime": regime}


def generate_full_report() -> dict:
    _REGIME_CACHE.clear()  # fresh regime each run
    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "date": date.today().isoformat(),
        "markets": {},
        "config": {
            "target_pct": TARGET_PCT,
            "atr_stop_mult": ATR_STOP_MULT,
            "min_rr": MIN_RR,
            "sector_cap": SECTOR_CAP,
            "earnings_blackout_days": EARNINGS_BLACKOUT_DAYS,
            "dollar_vol_min_usd": DOLLAR_VOL_MIN_USD,
            "portfolio_usd": PORTFOLIO_USD,
            "portfolio_risk_pct": PORTFOLIO_RISK_PCT,
        },
    }
    for market in ["US", "HK", "SG"]:
        logger.info(f"=== Screening {market} market ===")
        try:
            result = screen_market(market)
            report["markets"][market] = {
                "picks": result["picks"],
                "regime": result["regime"],
                "screened_at": datetime.utcnow().isoformat() + "Z",
                "status": "ok" if result["picks"] else "no_data",
                "count": len(result["picks"]),
            }
            logger.info(f"[{market}] Done — {len(result['picks'])} picks")
        except Exception as e:
            logger.error(f"[{market}] Failed: {e}")
            report["markets"][market] = {"picks": [], "regime": {}, "status": "error", "error": str(e)}
        time.sleep(3)
    return report
