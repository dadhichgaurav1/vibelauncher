# Specification: Integrate Critic Node

## Feature: Quality Gate via Critic Agent

### Overview
The critic node (`agents/nodes/critic.py`) is fully implemented with `run_critic()` and `should_retry()` functions but is never added to the graph. Integrate it as a quality gate that reviews content before human review, automatically requesting regeneration when quality is below threshold.

### User Stories
- As a user, I want AI-generated content to pass a quality check before I see it so that I only review high-quality drafts
- As a user, I want the agent to self-correct poor output so that I don't have to reject and give feedback on obviously bad content

---

## Functional Requirements

### FR-1: Add Critic Node to Graph
Wire the critic node into `agents/graph.py` between `content_creator` and `human_review`.

**Acceptance Criteria:**
- [ ] Critic node runs after `content_creator` (and after `media_generator`)
- [ ] Critic evaluates content using existing `run_critic()` rubric (completeness, accuracy, specificity, hook_quality, repost_worthy, x_rules_compliance, icp_alignment)
- [ ] Critic results stored in `state["critiques"]`

### FR-2: Auto-Retry on Low Quality
If critic scores are below threshold, loop back to `content_creator` with critic feedback instead of proceeding to human review.

**Acceptance Criteria:**
- [ ] `should_retry()` is called after critic evaluation
- [ ] If retry needed, content_creator is re-invoked with critic feedback injected (similar to `approval_feedback`)
- [ ] Maximum 2 auto-retries before proceeding to human review regardless (prevents infinite loops)
- [ ] `retry_counts` state field is incremented on each retry

### FR-3: Surface Critic Results to Frontend
Show the critic's assessment in the review panel so the user has context on content quality.

**Acceptance Criteria:**
- [ ] Critic scores sent to frontend via WebSocket `step_output` event
- [ ] Review panel displays quality scores (or a summary) alongside the content

---

## Success Criteria
- Content reaching human review has passed at least one quality gate
- Auto-retry loop terminates after max 2 retries
- No regressions in existing brainstorm → research → strategy → content flow

---

## Dependencies
- `agents/nodes/critic.py` (already implemented)
- `agents/state.py` fields: `critiques`, `retry_counts` (already defined)

## Assumptions
- Critic scoring thresholds in `should_retry()` are reasonable defaults
- Adding one extra LLM call per iteration is acceptable latency

---

## Completion Signal

### Implementation Checklist
- [ ] Critic node added to graph between media_generator and human_review
- [ ] Conditional edge: critic → content_creator (retry) or critic → human_review (pass)
- [ ] retry_counts incremented and checked (max 2)
- [ ] Critic feedback injected into content_creator on retry
- [ ] Critic scores emitted via WebSocket
- [ ] Frontend displays critic assessment in review panel

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [ ] Server starts without errors (`uvicorn server:app`)
- [ ] No Python syntax or import errors
- [ ] Graph compiles and all nodes are reachable

#### Functional Verification
- [ ] Full launch flow works end-to-end (product input → brainstorm → research → strategy → content → critic → review → publish)
- [ ] Critic node executes and produces scores
- [ ] Auto-retry triggers when scores are low (test by temporarily lowering threshold if needed)
- [ ] Retry loop caps at 2 iterations
- [ ] Content approval and publishing still work after critic integration

#### Console/Network Check
- [ ] No unhandled exceptions in server logs during full flow
- [ ] WebSocket messages for critic output are well-formed JSON

### Iteration Instructions

If ANY check fails:
1. Identify the specific issue
2. Fix the code
3. Restart the server and test the full flow
4. Verify all criteria
5. Commit and push
6. Check again

**Only when ALL checks pass, output:** `<promise>DONE</promise>`

NR_OF_TRIES: 1
