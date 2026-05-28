"""
Build/refresh the quality cache: Piotroski F-Score, FCF yield, next earnings date.

Run this LOCALLY (not on Render) — Yahoo blocks cloud IPs from these endpoints.
The output `data/quality_cache.json` is committed to git so production reads it.

Usage:
    python build_quality_cache.py            # rebuild all tickers
    python build_quality_cache.py AAPL MSFT  # rebuild only specified tickers

Piotroski F-Score (0-9, higher = stronger fundamentals):
  Profitability (4 pts):
    1. Net Income > 0
    2. Operating Cash Flow > 0
    3. Return on Assets increasing YoY
    4. CFO > Net Income (accrual quality)
  Leverage / liquidity (3 pts):
    5. Long-term debt ratio decreasing YoY
    6. Current ratio increasing YoY
    7. No new shares issued
  Efficiency (2 pts):
    8. Gross margin increasing YoY
    9. Asset turnover increasing YoY
"""

import json
import sys
import time
from pathlib import Path
from typing import Optional

import yfinance as yf
import pandas as pd

from stocks import US_STOCKS, HK_STOCKS, SG_STOCKS

CACHE_FILE = Path("data/quality_cache.json")
CACHE_FILE.parent.mkdir(exist_ok=True)


def _safe(v):
    try:
        f = float(v)
        if pd.isna(f) or f != f:
            return None
        return f
    except Exception:
        return None


def _col_pair(df: pd.DataFrame):
    """Return (most_recent_col, prior_col) from a yfinance financials DataFrame."""
    if df is None or df.empty or len(df.columns) < 2:
        return None, None
    cols = sorted(df.columns, reverse=True)  # newest first
    return cols[0], cols[1]


def _get(df, row_names, col):
    """Try several possible row names — yfinance row names vary."""
    if df is None or df.empty or col is None:
        return None
    for name in row_names:
        if name in df.index:
            return _safe(df.loc[name, col])
    return None


def piotroski(ticker_obj) -> dict:
    """Compute Piotroski 9-point F-score from yfinance financials."""
    try:
        fin = ticker_obj.financials                       # income statement
        bal = ticker_obj.balance_sheet
        cf  = ticker_obj.cashflow
    except Exception:
        return {"f_score": None, "components": {}}

    cur, prev = _col_pair(fin)
    cur_b, prev_b = _col_pair(bal)
    cur_c, prev_c = _col_pair(cf)
    if cur is None or prev is None:
        return {"f_score": None, "components": {}}

    comp = {}

    # 1. Net income > 0
    ni_cur  = _get(fin, ["Net Income", "Net Income Common Stockholders"], cur)
    ni_prev = _get(fin, ["Net Income", "Net Income Common Stockholders"], prev)
    comp["net_income_positive"] = 1 if (ni_cur and ni_cur > 0) else 0

    # 2. CFO > 0
    cfo_cur  = _get(cf, ["Operating Cash Flow", "Total Cash From Operating Activities", "Cash Flow From Continuing Operating Activities"], cur_c)
    cfo_prev = _get(cf, ["Operating Cash Flow", "Total Cash From Operating Activities", "Cash Flow From Continuing Operating Activities"], prev_c)
    comp["cfo_positive"] = 1 if (cfo_cur and cfo_cur > 0) else 0

    # 3. ROA increasing
    ta_cur  = _get(bal, ["Total Assets"], cur_b)
    ta_prev = _get(bal, ["Total Assets"], prev_b)
    if ni_cur and ni_prev and ta_cur and ta_prev and ta_cur > 0 and ta_prev > 0:
        comp["roa_increasing"] = 1 if (ni_cur / ta_cur) > (ni_prev / ta_prev) else 0
    else:
        comp["roa_increasing"] = 0

    # 4. CFO > Net Income (quality of earnings)
    comp["cfo_gt_ni"] = 1 if (cfo_cur and ni_cur and cfo_cur > ni_cur) else 0

    # 5. Long-term debt ratio decreasing
    ltd_cur  = _get(bal, ["Long Term Debt"], cur_b)
    ltd_prev = _get(bal, ["Long Term Debt"], prev_b)
    if ltd_cur is not None and ltd_prev is not None and ta_cur and ta_prev and ta_cur > 0 and ta_prev > 0:
        comp["ltd_decreasing"] = 1 if (ltd_cur / ta_cur) < (ltd_prev / ta_prev) else 0
    else:
        comp["ltd_decreasing"] = 0

    # 6. Current ratio increasing
    ca_cur  = _get(bal, ["Current Assets", "Total Current Assets"], cur_b)
    cl_cur  = _get(bal, ["Current Liabilities", "Total Current Liabilities"], cur_b)
    ca_prev = _get(bal, ["Current Assets", "Total Current Assets"], prev_b)
    cl_prev = _get(bal, ["Current Liabilities", "Total Current Liabilities"], prev_b)
    if ca_cur and cl_cur and ca_prev and cl_prev and cl_cur > 0 and cl_prev > 0:
        comp["current_ratio_up"] = 1 if (ca_cur / cl_cur) > (ca_prev / cl_prev) else 0
    else:
        comp["current_ratio_up"] = 0

    # 7. No new shares issued
    sh_cur  = _get(bal, ["Ordinary Shares Number", "Share Issued", "Common Stock"], cur_b)
    sh_prev = _get(bal, ["Ordinary Shares Number", "Share Issued", "Common Stock"], prev_b)
    if sh_cur and sh_prev:
        comp["no_new_shares"] = 1 if sh_cur <= sh_prev * 1.005 else 0  # ≤0.5% growth tolerated
    else:
        comp["no_new_shares"] = 0

    # 8. Gross margin increasing
    rev_cur  = _get(fin, ["Total Revenue", "Operating Revenue"], cur)
    rev_prev = _get(fin, ["Total Revenue", "Operating Revenue"], prev)
    gp_cur   = _get(fin, ["Gross Profit"], cur)
    gp_prev  = _get(fin, ["Gross Profit"], prev)
    if rev_cur and rev_prev and gp_cur and gp_prev and rev_cur > 0 and rev_prev > 0:
        comp["gross_margin_up"] = 1 if (gp_cur / rev_cur) > (gp_prev / rev_prev) else 0
    else:
        comp["gross_margin_up"] = 0

    # 9. Asset turnover increasing
    if rev_cur and rev_prev and ta_cur and ta_prev and ta_cur > 0 and ta_prev > 0:
        comp["asset_turnover_up"] = 1 if (rev_cur / ta_cur) > (rev_prev / ta_prev) else 0
    else:
        comp["asset_turnover_up"] = 0

    score = sum(comp.values())
    return {"f_score": score, "components": comp}


def fcf_yield(ticker_obj, fast_info) -> Optional[float]:
    """FCF / market cap × 100. Source: TTM FCF / current market cap."""
    try:
        cf = ticker_obj.cashflow
        cur, _ = _col_pair(cf)
        fcf = _get(cf, ["Free Cash Flow"], cur)
        if fcf is None:
            cfo = _get(cf, ["Operating Cash Flow", "Total Cash From Operating Activities"], cur)
            capex = _get(cf, ["Capital Expenditure", "Capital Expenditures"], cur)
            if cfo is not None and capex is not None:
                fcf = cfo + capex  # capex is usually negative in yf
        mc = _safe(fast_info.market_cap) if fast_info else None
        if fcf is not None and mc and mc > 0:
            return round(fcf / mc * 100, 2)
    except Exception:
        return None
    return None


def next_earnings(ticker_obj) -> Optional[str]:
    try:
        cal = ticker_obj.calendar
        if cal is None:
            return None
        if isinstance(cal, dict):
            ed = cal.get("Earnings Date")
            if isinstance(ed, list) and ed:
                return str(ed[0])[:10]
            if ed:
                return str(ed)[:10]
        elif isinstance(cal, pd.DataFrame) and not cal.empty:
            if "Earnings Date" in cal.index:
                val = cal.loc["Earnings Date"]
                first = val.iloc[0] if hasattr(val, "iloc") else val
                return str(first)[:10]
    except Exception:
        pass
    return None


def build(tickers: list):
    cache = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    total = len(tickers)
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{total}] {ticker:12s} …", end=" ", flush=True)
        try:
            t = yf.Ticker(ticker)
            fast = t.fast_info
            p = piotroski(t)
            fy = fcf_yield(t, fast)
            ne = next_earnings(t)
            cache[ticker] = {
                "f_score": p["f_score"],
                "f_components": p["components"],
                "fcf_yield": fy,
                "next_earnings": ne,
            }
            print(f"F={p['f_score']} FCFy={fy} earn={ne}")
        except Exception as e:
            print(f"FAIL: {e}")
            cache.setdefault(ticker, {})

        if i % 10 == 0:
            CACHE_FILE.write_text(json.dumps(cache, indent=2, sort_keys=True))
            print(f"  ↳ checkpoint saved ({i}/{total})")
        time.sleep(1.5)  # be nice to Yahoo

    CACHE_FILE.write_text(json.dumps(cache, indent=2, sort_keys=True))
    print(f"\nDone. Cache: {CACHE_FILE} ({len(cache)} entries)")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        tickers = sys.argv[1:]
    else:
        tickers = US_STOCKS + HK_STOCKS + SG_STOCKS
    build(tickers)
