# Specification: Smarter Deep Research

## Feature: Enhanced Research with Better Signal Extraction

### Overview
The deep research node generates 3 search queries and synthesizes results, but the quality depends heavily on search result richness. Improve the research pipeline to extract stronger signals: analyze competitor launches, find viral tweet patterns in the niche, and produce more actionable content strategy recommendations.

### User Stories
- As a user, I want the agent to find real viral examples in my niche so that generated content follows proven patterns
- As a user, I want competitor analysis that identifies gaps I can exploit in my launch narrative

---

## Functional Requirements

### FR-1: Expand Search Query Generation
Generate more diverse and targeted search queries.

**Acceptance Criteria:**
- [ ] Generate 5 search queries instead of 3 (more coverage)
- [ ] Query types: 1 competitor-focused, 1 audience pain-point focused, 1 viral content in niche, 1 product-category trending, 1 contrarian/debate angle
- [ ] Queries use X-native search syntax (e.g., `min_faves:100` to filter for high-engagement posts)

### FR-2: Viral Pattern Extraction
Analyze high-performing content more deeply.

**Acceptance Criteria:**
- [ ] For each search result set, identify the top 3 highest-engagement patterns (hook style, content structure, tone)
- [ ] Extract specific hook formulas that worked (not generic categories — actual patterns from real tweets found)
- [ ] Store extracted patterns in `research_brief["viral_patterns"]` with example references

### FR-3: Competitor Launch Analysis
Analyze how similar products were launched on X.

**Acceptance Criteria:**
- [ ] At least one search query targets direct competitors or similar products
- [ ] Research brief includes `competitor_analysis` with: what worked, what flopped, positioning gaps
- [ ] Content strategy accounts for competitor positioning (differentiate, don't duplicate)

### FR-4: Research Quality Score
Add a self-assessment of research quality to guide downstream decisions.

**Acceptance Criteria:**
- [ ] Research node outputs a `confidence_score` (0-1) based on how much signal was found
- [ ] If confidence is low (<0.3), the research brief explicitly notes "limited data — content should rely more on product strengths than market trends"
- [ ] Confidence score passed to content_creator so it can adjust strategy accordingly

---

## Success Criteria
- Research brief contains specific, actionable insights (not generic marketing advice)
- At least 2 real viral tweet patterns identified per launch
- Content strategy recommendations are grounded in discovered data

---

## Dependencies
- Browser client or httpx fallback for X search (already implemented)
- LLM for synthesis (already implemented)

## Assumptions
- X search results via extension or nitter fallback provide sufficient data
- 5 searches per launch is acceptable in terms of latency

---

## Completion Signal

### Implementation Checklist
- [ ] Search query generation expanded to 5 diverse queries
- [ ] Viral pattern extraction enhanced with specific hook analysis
- [ ] Competitor analysis integrated into research brief
- [ ] Confidence score added to research output
- [ ] Content creator receives and uses confidence score
- [ ] Strategy node accounts for competitor positioning

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [ ] Server starts without errors
- [ ] No Python syntax or import errors
- [ ] Research node produces valid JSON output

#### Functional Verification
- [ ] Full launch flow works end-to-end
- [ ] Research brief contains all new fields (viral_patterns with examples, competitor_analysis, confidence_score)
- [ ] Low-confidence scenario handled gracefully (content still generates)
- [ ] Step outputs show richer research data in frontend live feed

#### Console/Network Check
- [ ] No unhandled exceptions during research phase
- [ ] Search queries logged for debugging

### Iteration Instructions

If ANY check fails:
1. Identify the specific issue
2. Fix the code
3. Restart the server and test
4. Verify all criteria
5. Commit and push
6. Check again

**Only when ALL checks pass, output:** `<promise>DONE</promise>`
