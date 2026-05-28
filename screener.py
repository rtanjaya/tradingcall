"""
Core stock screening engine — yfinance 1.x compatible.
Batched price downloads + fast_info for speed, info only for top candidates.
"""

import time
import logging
from datetime import datetime, date
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf
import pytz

from stocks import MARKET_CONFIG, COMPANY_NAMES

logger = logging.getLogger(__name__)

BATCH_SIZE = 25       # tickers per yf.download call
BATCH_DELAY = 2.0     # seconds between batches
INFO_DELAY = 0.8      # seconds between .info calls
MAX_INFO_CALLS = 40   # fetch fundamentals for top N candidates only


# ── Technical Indicators ───────────────────────────────────────────────────────

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


# ── Scoring ────────────────────────────────────────────────────────────────────

def score_stock(m: dict) -> float:
    score = 0.0

    rsi = m.get("rsi")
    if rsi and not pd.isna(rsi):
        if 28 <= rsi <= 42:
            score += 25
        elif 20 <= rsi < 28:
            score += 15
        elif 42 < rsi <= 52:
            score += 12

    pos52 = m.get("pos_52w")
    if pos52 is not None and not pd.isna(pos52):
        if pos52 <= 20:
            score += 20
        elif pos52 <= 35:
            score += 16
        elif pos52 <= 50:
            score += 10
        elif pos52 <= 65:
            score += 4

    vs_ma50 = m.get("vs_ma50_pct")
    if vs_ma50 is not None and not pd.isna(vs_ma50):
        if -15 <= vs_ma50 <= -2:
            score += 18
        elif -2 < vs_ma50 <= 2:
            score += 8
        elif vs_ma50 < -15:
            score += 5

    pe = m.get("pe")
    if pe and not pd.isna(pe):
        if 0 < pe <= 12:
            score += 15
        elif 12 < pe <= 18:
            score += 10
        elif 18 < pe <= 25:
            score += 5

    pb = m.get("pb")
    if pb and not pd.isna(pb):
        if 0 < pb <= 1.5:
            score += 12
        elif 1.5 < pb <= 2.5:
            score += 7
        elif 2.5 < pb <= 3.5:
            score += 3

    atr = m.get("atr_pct")
    if atr and not pd.isna(atr):
        if atr >= 3.0:
            score += 10
        elif atr >= 2.0:
            score += 8
        elif atr >= 1.5:
            score += 5

    return round(score, 1)


def generate_rationale(m: dict) -> str:
    parts = []
    rsi = m.get("rsi")
    if rsi and not pd.isna(rsi):
        if rsi < 35:
            parts.append(f"RSI {rsi:.0f} — deeply oversold")
        elif rsi < 50:
            parts.append(f"RSI {rsi:.0f} — oversold, reversal setup")
    pos52 = m.get("pos_52w")
    if pos52 is not None and not pd.isna(pos52) and pos52 <= 35:
        parts.append(f"near 52-week low ({pos52:.0f}% of range)")
    vs_ma = m.get("vs_ma50_pct")
    if vs_ma is not None and not pd.isna(vs_ma) and vs_ma <= -3:
        parts.append(f"{abs(vs_ma):.1f}% below 50-day MA")
    pe = m.get("pe")
    if pe and not pd.isna(pe) and 0 < pe < 20:
        parts.append(f"P/E {pe:.1f}x")
    pb = m.get("pb")
    if pb and not pd.isna(pb) and 0 < pb < 2:
        parts.append(f"P/B {pb:.1f}x")
    atr = m.get("atr_pct")
    if atr and not pd.isna(atr) and atr >= 1.5:
        parts.append(f"avg swing {atr:.1f}%/day")
    return ". ".join(parts) if parts else "Meets multi-factor value + momentum criteria"


# ── Data Fetching ──────────────────────────────────────────────────────────────

def _safe(val, default=None):
    try:
        f = float(val)
        return None if (pd.isna(f) or np.isinf(f)) else f
    except Exception:
        return default


def fetch_batch_prices(tickers: list, period: str = "6mo") -> dict:
    """
    yf.download in batches of BATCH_SIZE.
    Returns {ticker: DataFrame(Open,High,Low,Close,Volume)}.
    yfinance 1.x columns: MultiIndex (field, ticker).
    """
    results = {}
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i: i + BATCH_SIZE]
        try:
            raw = yf.download(
                batch,
                period=period,
                interval="1d",
                auto_adjust=True,
                progress=False,
                group_by="column",  # (field, ticker) MultiIndex
            )
            if raw.empty:
                continue

            for ticker in batch:
                try:
                    if len(batch) == 1:
                        df = raw.copy()
                        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
                    else:
                        # MultiIndex: columns are (field, ticker)
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
    """Use fast_info for market cap, 52w range, MA50 — no heavy API call."""
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


def fetch_fundamentals(ticker: str) -> dict:
    """Fetch P/E, P/B, name, sector from yfinance info. Slow — use sparingly.
    Always seeds name from COMPANY_NAMES lookup first so HK/SG names always show."""
    # Start with our hardcoded lookup — guaranteed to show the right name
    base_name = COMPANY_NAMES.get(ticker, "")
    try:
        info = yf.Ticker(ticker).info
        api_name = info.get("longName") or info.get("shortName") or ""
        return {
            "name": base_name or api_name or ticker,
            "sector": info.get("sector", ""),
            "pe": _safe(info.get("trailingPE") or info.get("forwardPE")),
            "pb": _safe(info.get("priceToBook")),
            "roe": _safe(info.get("returnOnEquity")),
        }
    except Exception:
        return {"name": ticker, "sector": ""}


# ── Main Screener ──────────────────────────────────────────────────────────────

def screen_market(market: str, top_n: int = 10) -> list:
    config = MARKET_CONFIG[market]
    tickers = config["tickers"]
    currency = config["currency"]

    logger.info(f"[{market}] Fetching price data for {len(tickers)} tickers…")
    price_data = fetch_batch_prices(tickers)
    logger.info(f"[{market}] Got price data for {len(price_data)} tickers")

    candidates = []
    for ticker, df in price_data.items():
        try:
            close = df["Close"].dropna()
            if len(close) < 20:
                continue
            high = df["High"].dropna()
            low = df["Low"].dropna()

            current_price = float(close.iloc[-1])
            prev_close = float(close.iloc[-2]) if len(close) >= 2 else current_price
            day_change_pct = round((current_price - prev_close) / prev_close * 100, 2) if prev_close else 0

            rsi = calc_rsi(close)
            atr_pct = calc_atr_pct(high, low, close) if "High" in df.columns else float("nan")

            ma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
            vs_ma50 = round((current_price - ma50) / ma50 * 100, 2) if ma50 and ma50 > 0 else None

            low52 = float(low.tail(252).min()) if len(low) >= 20 else float(low.min())
            high52 = float(high.tail(252).max()) if len(high) >= 20 else float(high.max())
            pos52 = pct_of_range(current_price, low52, high52)

            candidates.append({
                "ticker": ticker,
                "name": COMPANY_NAMES.get(ticker, ""),  # seed name immediately
                "price": current_price,
                "day_change_pct": day_change_pct,
                "rsi": rsi,
                "atr_pct": atr_pct,
                "vs_ma50_pct": vs_ma50,
                "pos_52w": pos52,
                "low_52w": round(low52, 4),
                "high_52w": round(high52, 4),
                "currency": currency,
            })
        except Exception as e:
            logger.warning(f"[{market}] Error processing {ticker}: {e}")
            continue

    if not candidates:
        return []

    # Pre-filter: RSI < 58, not already extended above 52w range
    candidates = [c for c in candidates if
                  (pd.isna(c["rsi"]) or c["rsi"] < 58) and
                  c["pos_52w"] < 65]

    # Pre-sort before expensive calls
    candidates.sort(key=lambda x: (x.get("pos_52w") or 100, x.get("rsi") or 100))
    top_pool = candidates[:MAX_INFO_CALLS]

    # Enrich with fast_info (market cap filter) + fundamentals for top candidates
    logger.info(f"[{market}] Enriching {len(top_pool)} candidates…")
    enriched = []
    for i, c in enumerate(top_pool):
        fi = fetch_fast_info(c["ticker"])
        mc = fi.get("market_cap")

        # Market cap gate: >= $800M USD equivalent
        if mc:
            mc_usd = mc / 7.8 if currency == "HKD" else mc / 1.35 if currency == "SGD" else mc
            if mc_usd < 800_000_000:
                continue
        c["market_cap_raw"] = mc
        c.update(fi)
        enriched.append(c)
        if i % 5 == 4:
            time.sleep(0.5)

    # Fetch fundamentals (P/E, P/B) for final scoring
    for i, c in enumerate(enriched[:25]):
        fund = fetch_fundamentals(c["ticker"])
        c.update(fund)
        # Skip negative P/E (loss-making)
        if c.get("pe") and c["pe"] < 0:
            c["_skip"] = True
        c["score"] = score_stock(c)
        c["rationale"] = generate_rationale(c)
        time.sleep(INFO_DELAY)

    # Score remaining without fundamentals
    for c in enriched[25:]:
        c.setdefault("name", COMPANY_NAMES.get(c["ticker"], "") or c["ticker"])
        c.setdefault("sector", "")
        c["score"] = score_stock(c)
        c["rationale"] = generate_rationale(c)

    final = [c for c in enriched if not c.get("_skip")]
    final.sort(key=lambda x: x["score"], reverse=True)

    results = []
    for rank, c in enumerate(final[:top_n], 1):
        mc = c.get("market_cap_raw")
        if mc:
            if mc >= 1e12:
                mc_display = f"{mc/1e12:.1f}T"
            elif mc >= 1e9:
                mc_display = f"{mc/1e9:.1f}B"
            else:
                mc_display = f"{mc/1e6:.0f}M"
        else:
            mc_display = "—"

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
            "score": c["score"],
            "rationale": c["rationale"],
            "signal": "SWING BUY" if c["score"] >= 50 else "WATCH",
        })

    return results


def generate_full_report() -> dict:
    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "date": date.today().isoformat(),
        "markets": {},
    }
    for market in ["US", "HK", "SG"]:
        logger.info(f"=== Screening {market} market ===")
        try:
            picks = screen_market(market)
            report["markets"][market] = {
                "picks": picks,
                "screened_at": datetime.utcnow().isoformat() + "Z",
                "status": "ok" if picks else "no_data",
                "count": len(picks),
            }
            logger.info(f"[{market}] Done — {len(picks)} picks")
        except Exception as e:
            logger.error(f"[{market}] Failed: {e}")
            report["markets"][market] = {"picks": [], "status": "error", "error": str(e)}
        time.sleep(3)
    return report
