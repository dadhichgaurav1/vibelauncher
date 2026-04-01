# Specification: Agent Memory & Learning

## Feature: Cross-Session Learning from Past Launches

### Overview
Each launch currently starts from scratch with no knowledge of previous launches. Add a lightweight memory system so the agent learns from past successes and failures — which hooks performed well, what content styles the user prefers, and what critique patterns recur.

### User Stories
- As a repeat user, I want the agent to remember what content style I prefer so that each launch improves on the last
- As a user, I want the agent to learn from approval/rejection patterns so it stops making the same mistakes

---

## Functional Requirements

### FR-1: Launch Outcome Storage
Store key outcomes from each completed launch.

**Acceptance Criteria:**
- [ ] New SQLite table `launch_memory` with fields: launch_id, product_name, hook_used, content_style, formats_selected, was_approved_first_try (bool), rejection_feedback (if any), critic_scores, created_at
- [ ] Publisher node writes a memory record after successful publish
- [ ] Rejection feedback from human review is captured with the content that was rejected

### FR-2: Memory Retrieval in Content Creation
Inject relevant past launch data into content creation prompts.

**Acceptance Criteria:**
- [ ] Content creator queries last 10 launch memories before generating
- [ ] Prompt includes: "User previously preferred [style/hooks]. Rejections were for: [feedback patterns]"
- [ ] If no memories exist (first launch), behavior is unchanged
- [ ] Memory context is concise — summarized, not raw dumps

### FR-3: Style Preference Tracking
Track and apply user content preferences.

**Acceptance Criteria:**
- [ ] Track which formats the user selects most often (tweet vs thread vs images vs video)
- [ ] Track tone preferences (inferred from approval patterns and brainstorm answers)
- [ ] Strategy node uses preference data to weight content format recommendations
- [ ] Preferences are suggestions, not hard constraints — user can always override

---

## Success Criteria
- By the 3rd launch, content generation reflects patterns from previous approvals
- Rejection reasons from launch N do not recur in launch N+1
- First-try approval rate improves over successive launches

---

## Dependencies
- SQLite database (already used for sessions and tokens)
- Spec 001 (critic integration) is helpful but not required

## Assumptions
- 10 past launches is sufficient context for pattern detection
- Summarized memory fits within LLM context limits without issue

---

## Completion Signal

### Implementation Checklist
- [ ] `launch_memory` table created in database.py
- [ ] Memory record written after successful publish
- [ ] Rejection feedback stored when content is rejected
- [ ] Content creator retrieves and uses past memories
- [ ] Strategy node uses format/tone preferences
- [ ] Memory retrieval is concise and token-efficient

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [ ] Server starts without errors
- [ ] Database migrations/table creation works on fresh DB
- [ ] No Python syntax or import errors

#### Functional Verification
- [ ] First launch works identically to current behavior (no memories)
- [ ] After one completed launch, memory record exists in DB
- [ ] Second launch's content creator prompt includes memory context
- [ ] Rejection feedback is stored and retrieved correctly

#### Console/Network Check
- [ ] No unhandled exceptions during memory read/write
- [ ] Memory queries are fast (<100ms)

### Iteration Instructions

If ANY check fails:
1. Identify the specific issue
2. Fix the code
3. Restart the server and test
4. Verify all criteria
5. Commit and push
6. Check again

**Only when ALL checks pass, output:** `<promise>DONE</promise>`
