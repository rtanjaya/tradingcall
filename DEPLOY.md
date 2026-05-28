# TradingCall — Deployment Guide

## Run Locally

```bash
cd tradingcall
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
```

Open: http://localhost:8000

## Deploy to Render.com (free, internet-accessible)

1. Push this folder to a GitHub repo
2. Go to https://render.com → New → Web Service
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` — just click **Deploy**
5. Your URL will be: `https://tradingcall-xxxx.onrender.com`

> Free tier sleeps after 15 min inactivity. Upgrade to Starter ($7/mo) for always-on.

## Report Schedule

Reports auto-generate at:
- **22:00 UTC** (before US next-day open)
- **01:00 UTC** (before Asia open)

You can also hit the **⟳ Refresh Report** button in the dashboard anytime.

## Endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Dashboard UI |
| `GET /api/report` | Latest report JSON |
| `GET /api/refresh` | Trigger new report generation |
| `GET /api/status` | Generation status + last report time |
