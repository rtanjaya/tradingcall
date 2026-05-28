"""
TradingCall — Daily swing-trade signal dashboard
FastAPI backend with scheduled report generation.
"""

import json
import logging
import os
from datetime import datetime, time as dtime
from pathlib import Path
from typing import Optional

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from screener import generate_full_report

# ── Config ─────────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CACHE_DIR = Path("data")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_FILE = CACHE_DIR / "latest_report.json"

app = FastAPI(title="TradingCall", version="1.0.0")
templates = Jinja2Templates(directory="templates")

# ── Report Cache ───────────────────────────────────────────────────────────────

_report_generating = False


def load_cached_report() -> Optional[dict]:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            return None
    return None


def save_report(report: dict):
    CACHE_FILE.write_text(json.dumps(report, indent=2))
    # Also save a dated archive copy
    dated = CACHE_DIR / f"report_{report['date']}.json"
    dated.write_text(json.dumps(report, indent=2))


def run_screener():
    global _report_generating
    if _report_generating:
        logger.info("Screener already running — skipping")
        return
    _report_generating = True
    try:
        logger.info("Starting daily report generation…")
        report = generate_full_report()
        save_report(report)
        logger.info("Report saved successfully")
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
    finally:
        _report_generating = False


# ── Scheduler ──────────────────────────────────────────────────────────────────
# Runs at these UTC times to cover pre-market for each session:
#   06:30 UTC = 14:30 SGT / 14:30 HKT  (before SG/HK market hours end, for next-day)
#   22:00 UTC = 18:00 ET (after US close — pre-next-day US report)

scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_job(run_screener, CronTrigger(hour=22, minute=0), id="us_report")
scheduler.add_job(run_screener, CronTrigger(hour=1, minute=0), id="asia_report")


# ── Startup / Shutdown ─────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    scheduler.start()
    if not CACHE_FILE.exists():
        logger.info("No cached report found — generating initial report in background…")
        import threading
        t = threading.Thread(target=run_screener, daemon=True)
        t.start()


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown(wait=False)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/report")
async def get_report():
    report = load_cached_report()
    if not report:
        if _report_generating:
            return JSONResponse({"status": "generating", "message": "Report is being generated. Check back in a few minutes."})
        raise HTTPException(status_code=404, detail="No report available yet. Use /api/refresh to generate one.")
    return JSONResponse({"status": "ok", "generating": _report_generating, "report": report})


@app.get("/api/refresh")
async def refresh_report(background_tasks: BackgroundTasks):
    if _report_generating:
        return JSONResponse({"status": "already_running", "message": "Report generation already in progress."})
    background_tasks.add_task(run_screener)
    return JSONResponse({"status": "started", "message": "Report generation started. Refresh in 3-5 minutes."})


@app.get("/api/status")
async def status():
    report = load_cached_report()
    return JSONResponse({
        "generating": _report_generating,
        "last_report": report["generated_at"] if report else None,
        "report_date": report["date"] if report else None,
    })
