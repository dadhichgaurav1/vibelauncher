# Specification: Retry Logic & Error Handling

## Feature: Resilient Agent Pipeline with Retries

### Overview
The agent pipeline currently has no retry logic for failed LLM calls, API errors (Gemini image/video, X API), or transient failures. The `retry_counts` field exists in state but is never used. Add structured retry logic and surface errors clearly to the frontend.

### User Stories
- As a user, I want the agent to automatically retry when an API call fails transiently so that I don't have to restart the entire flow
- As a user, I want to see clear error messages when something goes wrong so that I understand what happened

---

## Functional Requirements

### FR-1: LLM Call Retries
Add retry logic to the base LLM functions in `agents/nodes/base.py`.

**Acceptance Criteria:**
- [ ] `llm()` and `llm_json()` retry up to 3 times on transient errors (rate limits, timeouts, 5xx)
- [ ] Exponential backoff between retries (1s, 2s, 4s)
- [ ] Non-retryable errors (auth failures, invalid request) fail immediately
- [ ] Each retry is logged with the error reason

### FR-2: Media Generation Retries
Add retry handling for Gemini Imagen and Veo API calls in `agents/nodes/media_generator.py`.

**Acceptance Criteria:**
- [ ] Image generation retries up to 2 times on failure
- [ ] Video generation polling already has retry logic (30 attempts) — ensure it handles HTTP errors gracefully during polling
- [ ] If media generation fails after all retries, the flow continues with content but without media (graceful degradation) rather than crashing
- [ ] Missing media is flagged in the content_ready WebSocket message so the review panel can show "image/video generation failed"

### FR-3: Publisher Retries
Add retry handling for X API calls in `agents/tools/x_api.py` and `agents/nodes/publisher.py`.

**Acceptance Criteria:**
- [ ] Tweet posting retries up to 2 times on transient X API errors
- [ ] Media upload retries up to 2 times
- [ ] Rate limit errors (429) wait for the reset window before retrying
- [ ] Auth errors (401/403) fail immediately with a clear message to reconnect X account

### FR-4: Error Surfacing to Frontend
Improve how errors reach the user.

**Acceptance Criteria:**
- [ ] Node-level errors sent as `step_output` events with error context (which node, what failed, whether retries were exhausted)
- [ ] Fatal errors (all retries exhausted) send a `phase: "error"` event with actionable message
- [ ] Non-fatal errors (media failed but content OK) allow the flow to continue

---

## Success Criteria
- A transient LLM API failure does not crash the pipeline
- A failed image generation does not block tweet publishing
- Users see actionable error messages, not stack traces

---

## Dependencies
- None — works on existing codebase

## Assumptions
- Transient errors are the most common failure mode
- 3 retries with backoff is sufficient for most transient issues

---

## Completion Signal

### Implementation Checklist
- [ ] Retry decorator or utility added for async functions
- [ ] `llm()` and `llm_json()` in base.py wrapped with retry logic
- [ ] Media generation in media_generator.py handles failures gracefully
- [ ] Publisher and X API calls have retry logic
- [ ] Error events sent via WebSocket with actionable context
- [ ] Graceful degradation: missing media doesn't block publishing

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [ ] Server starts without errors
- [ ] No Python syntax or import errors
- [ ] All imports resolve correctly

#### Functional Verification
- [ ] Full launch flow works end-to-end when all services are healthy
- [ ] Simulated LLM failure (e.g., temporarily invalid API key) produces a clear error message to frontend, not a crash
- [ ] If image generation fails, the flow still reaches human review with text content

#### Console/Network Check
- [ ] No unhandled exceptions in server logs during normal flow
- [ ] Retry attempts are logged with clear context

### Iteration Instructions

If ANY check fails:
1. Identify the specific issue
2. Fix the code
3. Restart the server and test
4. Verify all criteria
5. Commit and push
6. Check again

**Only when ALL checks pass, output:** `<promise>DONE</promise>`
