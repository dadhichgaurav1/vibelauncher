# Specification: Video Publishing to X

## Feature: Attach Generated Videos to Tweets

### Overview
The media generator creates videos via Google Veo API, but the publisher node only uploads images to X. Videos are generated but never attached to tweets. Implement video upload and attachment so that video content actually gets published.

### User Stories
- As a user, I want my AI-generated video to be attached to my tweet so that I get the 2-4x reach boost from native video
- As a user, I want to preview the generated video before publishing so I know what will be posted

---

## Functional Requirements

### FR-1: Video Upload to X Media API
Add video upload support to `agents/tools/x_api.py`.

**Acceptance Criteria:**
- [ ] New function `upload_video(video_data)` that uploads video via X API v1.1 chunked media upload endpoint
- [ ] Handles the INIT → APPEND → FINALIZE → STATUS flow for chunked upload
- [ ] Polls processing status until video is ready (X processes uploaded video async)
- [ ] Returns `media_id` on success
- [ ] Supports videos up to 15 seconds / 512MB (X limits for tweets)

### FR-2: Attach Video to Tweet in Publisher
Update `agents/nodes/publisher.py` to attach video when available.

**Acceptance Criteria:**
- [ ] If `content.video` exists with a valid URL/data and user selected "video" format, upload and attach to tweet
- [ ] Video can be attached alongside the tweet text (same as images)
- [ ] If video upload fails, fall back to posting tweet without video (log warning)
- [ ] Only one video per tweet (X limitation) — if both images and video selected, video takes priority on the main tweet, images go on first_reply

### FR-3: Video Data Handling
Ensure video data from Veo API flows correctly to the publisher.

**Acceptance Criteria:**
- [ ] Video URL/data from media_generator is in a format consumable by the X upload API (binary data or downloadable URL)
- [ ] If Veo returns a GCS URI, download the video bytes before uploading to X
- [ ] Video content type is correctly set (video/mp4)

---

## Success Criteria
- A generated video is successfully posted as native video on X
- Video appears in the tweet when viewed on X
- Fallback works: if video upload fails, tweet still posts with text only

---

## Dependencies
- Working Veo video generation (already implemented in media_generator.py)
- X API OAuth tokens (already implemented)
- X API v1.1 media upload endpoint supports video (requires elevated access or basic tier)

## Assumptions
- The X API tier in use supports video upload (v1.1 chunked upload)
- Veo-generated videos are under X's size/duration limits (8 seconds, should be well under 512MB)

---

## Completion Signal

### Implementation Checklist
- [ ] `upload_video()` function added to x_api.py with chunked upload flow
- [ ] Publisher node calls `upload_video()` when video format is selected
- [ ] GCS URI or base64 video data converted to uploadable bytes
- [ ] Fallback logic: video upload failure doesn't block tweet posting
- [ ] Video vs image priority logic implemented (video on main tweet, images on reply)

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [ ] Server starts without errors
- [ ] No Python syntax or import errors
- [ ] All new functions have proper error handling

#### Functional Verification
- [ ] Full launch flow works with video format selected
- [ ] Video upload function handles the chunked upload protocol correctly
- [ ] If video data is unavailable, publisher gracefully falls back to text-only
- [ ] Images and video together: video on main tweet, images on first_reply

#### Console/Network Check
- [ ] No unhandled exceptions during video upload flow
- [ ] X API responses logged for debugging

### Iteration Instructions

If ANY check fails:
1. Identify the specific issue
2. Fix the code
3. Restart the server and test
4. Verify all criteria
5. Commit and push
6. Check again

**Only when ALL checks pass, output:** `<promise>DONE</promise>`
