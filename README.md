# Vibe Launcher

AI-powered agent system that automates social media launch campaigns on X (Twitter) for software products. Give it a product URL, docs, or transcript — it generates a full launch strategy, content (tweets, threads, images, video), and publishes directly to X.

## How It Works

1. **Product Analyst** — Extracts product brief from your URL, markdown, transcript, or README
2. **Brainstorm** — Generates targeted questions about your ICP, narrative, and tone *(human-in-the-loop)*
3. **Deep Research** — Analyzes market context, competitors, and audience sentiment
4. **Strategy** — Creates launch narrative, posting schedule, and visual brief
5. **Content Creator** — Generates tweets, threads (7-10 tweets), image prompts, and video prompts
6. **Media Generator** — Creates AI-generated images (Gemini) and video (Veo)
7. **Human Review** — Approve, reject with feedback, or request regeneration *(human-in-the-loop)*
8. **Publisher** — Posts to X with media, supports scheduled posting

## Architecture

```
vibelauncher/
├── apps/web/          # Next.js 15 frontend
├── apps/extension/    # Chrome extension (Manifest V3)
└── agents/            # FastAPI + LangGraph backend
```

- **Frontend:** Next.js 15, React, TypeScript, Tailwind CSS, Radix UI, Zustand, Framer Motion
- **Backend:** FastAPI, LangGraph (stateful agent workflow), OpenAI, Google Gemini, Tweepy
- **Extension:** Chrome extension with "Launch This" button for builder platforms (Lovable, Replit, Cursor, Vercel, Netlify)
- **Real-time:** WebSocket connections for live progress tracking and human-in-the-loop interactions
- **Database:** SQLite for session state and LangGraph checkpoints

## Setup

### Prerequisites

- Node.js 20+
- Python 3.11+
- Chrome browser (for the extension)

### 1. Web App

```bash
cd apps/web
npm install
npm run dev
# http://localhost:3000
```

### 2. Agent Backend

```bash
cd agents
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
# http://localhost:8000
```

### 3. Chrome Extension

```bash
cd apps/extension
npm install
npm run build
```

Then load as an unpacked extension in `chrome://extensions` (enable Developer mode).

### 4. Run Everything

```bash
npm run dev  # Runs web (port 3000) + agents (port 8000) concurrently
```

## Environment Variables

Create `agents/.env`:

```env
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.4

# Google Gemini (image generation)
GEMINI_API_KEY=...

# X (Twitter) OAuth
X_CONSUMER_KEY=...
X_CONSUMER_SECRET=...
X_BEARER_TOKEN=...
X_CALLBACK_URL=http://localhost:3000/api/auth/x/callback

# App
SECRET_KEY=dev-secret-change-in-prod
DB_PATH=./vibelauncher.db
```

## Key Features

- **Multi-input analysis** — URL, markdown, transcript, README, or any combination
- **Human-in-the-loop** — Brainstorm questions and content review with approve/reject/regenerate
- **Full content suite** — Launch tweet, thread, AI images, AI video
- **X integration** — OAuth 1.0a, direct posting, media upload, scheduled posting
- **Live progress** — Real-time WebSocket updates with stage-by-stage tracking
- **Chrome extension** — One-click "Launch This" on builder platforms
- **Checkpointed workflow** — Resume interrupted sessions via LangGraph checkpoints
