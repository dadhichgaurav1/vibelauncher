# Claude Code Instructions

**Read the constitution**: `.specify/memory/constitution.md`

It contains the full project context, principles, tech stack, and Ralph Wiggum workflow configuration.

## Project: Vibe Launcher

Full-stack monorepo: Next.js frontend (`apps/web`), FastAPI backend (`agents/`), Chrome extension (`apps/extension`).

## Quick Commands

```bash
# Dev
npm run dev:web          # Frontend on :3000
npm run dev:agents       # Backend on :8000
npm run dev              # Both concurrently

# Build
cd apps/web && npm run build
cd apps/extension && node build.js
```
