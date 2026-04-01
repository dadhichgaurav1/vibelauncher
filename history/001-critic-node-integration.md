# 001 — Critic Node Integration

## What was done
- Added `critic` node to `agents/graph.py` between `media_generator` and `human_review`
- Added conditional routing: critic → content_creator (retry) or critic → human_review (pass)
- Added `critic_feedback` field to `VibeLaunchState` in `state.py`
- Updated `content_creator_node` to combine `approval_feedback` and `critic_feedback`
- Critic scores emitted via WebSocket `step_output` event
- Frontend `ReviewPanel` shows quality gate results (score, issues, suggestions)
- Frontend `page.tsx` captures critic data from step_output and passes to ReviewPanel

## Key decisions
- Critic only runs on the "content" stage (not product_brief, research, strategy) to keep the first implementation simple and focused on the spec requirements
- Retry routing uses `critic_feedback` field as signal: if set, route to content_creator; if not, proceed
- Max 2 retries enforced by `should_retry()` which already existed in `critic.py`
- Critic feedback is combined with approval feedback using `" | ".join()` for simplicity

## Verified
- Python syntax OK for all modified files
- Graph compiles with critic node: `['__start__', 'product_analyst', 'brainstorm', 'deep_research', 'strategy', 'content_creator', 'media_generator', 'critic', 'human_review', 'publisher']`
- Next.js frontend builds successfully with no type errors
