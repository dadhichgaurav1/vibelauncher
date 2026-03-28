# Vibe Launcher — Setup

## Prerequisites
- Node.js 20+
- Python 3.11+
- Chrome browser

## 1. Web App

```bash
cd apps/web
npm install
npm run dev
# Runs on http://localhost:3000
```

## 2. Agent Backend

```bash
cd agents
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
# Runs on http://localhost:8000
```

## 3. Chrome Extension

```bash
cd apps/extension
npm install
node build.js
```

Then in Chrome:
1. Go to `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `apps/extension` folder

## 4. X OAuth

Visit `http://localhost:3000` → click "Connect X account" → authorize in Twitter.

## Environment

All keys are pre-configured in `agents/.env`. Do not commit this file.
