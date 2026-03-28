"""
FastAPI server.
Handles: launch creation, WebSocket sessions, X OAuth flow.
"""

from __future__ import annotations
import uuid
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from config import X_CONSUMER_KEY, X_CONSUMER_SECRET
from db.database import init_db, create_session, update_session, get_session, save_x_tokens, get_x_tokens
from graph import graph
from tools.ws_notifier import register_connection, unregister_connection
from tools.browser_client import register_extension, unregister_extension, receive_browser_result
from tools.x_api import get_request_token, exchange_verifier_for_tokens

app = FastAPI(title="Vibe Launcher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "chrome-extension://*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for OAuth request tokens (short-lived)
_oauth_request_tokens: dict[str, str] = {}  # token -> secret

# In-memory store for pending human responses: launch_id -> asyncio.Queue
_human_response_queues: dict[str, asyncio.Queue] = {}


@app.on_event("startup")
async def startup():
    init_db()


# ─── Launch endpoints ─────────────────────────────────────────────────────────

class LaunchInput(BaseModel):
    url: Optional[str] = None
    markdown: Optional[str] = None
    transcript: Optional[str] = None
    readme: Optional[str] = None


@app.post("/launch")
async def create_launch(body: LaunchInput):
    if not any([body.url, body.markdown, body.transcript, body.readme]):
        raise HTTPException(status_code=400, detail="At least one input required")

    launch_id = str(uuid.uuid4())
    user_id = "demo_user"  # TODO: real auth

    initial_state = {
        "launch_id": launch_id,
        "user_id": user_id,
        "ws_channel": launch_id,
        "input_url": body.url,
        "input_markdown": body.markdown,
        "input_transcript": body.transcript,
        "input_readme": body.readme,
        "product": None,
        "brainstorm_prompt": None,
        "brainstorm_responses": None,
        "research_brief": None,
        "strategy": None,
        "content": None,
        "critiques": None,
        "retry_counts": {},
        "agent_traces": {},
        "x_access_token": None,
        "x_access_token_secret": None,
        "approved": False,
        "approval_feedback": None,
        "published": None,
        "error": None,
    }

    # Get user's X tokens if they've connected
    x_tokens = get_x_tokens(user_id)
    if x_tokens:
        initial_state["x_access_token"] = x_tokens["access_token"]
        initial_state["x_access_token_secret"] = x_tokens["access_token_secret"]

    create_session(launch_id, user_id, initial_state)
    _human_response_queues[launch_id] = asyncio.Queue()

    return {"launch_id": launch_id}


# ─── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws/launch/{launch_id}")
async def launch_websocket(websocket: WebSocket, launch_id: str):
    await websocket.accept()
    register_connection(launch_id, websocket)

    session = get_session(launch_id)
    if not session:
        await websocket.send_text(json.dumps({"type": "error", "data": "Session not found"}))
        await websocket.close()
        return

    # Send initial session data
    await websocket.send_text(json.dumps({"type": "phase", "data": "loading"}))

    try:
        # Run graph in background task
        graph_task = asyncio.create_task(
            _run_graph(launch_id, session["state"], websocket)
        )

        # Listen for messages from frontend
        while True:
            try:
                msg_text = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                msg = json.loads(msg_text)

                if msg["type"] == "brainstorm_response":
                    q = _human_response_queues.get(launch_id)
                    if q:
                        await q.put({"type": "brainstorm", "data": msg["data"]})

                elif msg["type"] == "content_approval":
                    q = _human_response_queues.get(launch_id)
                    if q:
                        await q.put({
                            "type": "approval",
                            "approved": msg.get("approved", False),
                            "feedback": msg.get("feedback", ""),
                        })

                elif msg["type"] == "browser_result":
                    await receive_browser_result(launch_id, msg["data"])

            except asyncio.TimeoutError:
                pass

            if graph_task.done():
                break

    except WebSocketDisconnect:
        pass
    finally:
        unregister_connection(launch_id)
        graph_task.cancel()


async def _run_graph(launch_id: str, initial_state: dict, websocket: WebSocket):
    """Run the LangGraph graph, handling human interrupts."""
    config = {"configurable": {"thread_id": launch_id}}
    q = _human_response_queues.get(launch_id)

    try:
        # Run until first interrupt (brainstorm)
        async for event in graph.astream(initial_state, config):
            pass

        # Check if interrupted at brainstorm
        graph_state = graph.get_state(config)

        if graph_state.next and "human_review" not in graph_state.next:
            # Waiting at brainstorm — wait for human response
            if q:
                response = await asyncio.wait_for(q.get(), timeout=600)  # 10 min timeout
                if response["type"] == "brainstorm":
                    # Resume with brainstorm responses
                    graph.update_state(
                        config,
                        {"brainstorm_responses": response["data"]},
                    )
                    # Continue running
                    async for event in graph.astream(None, config):
                        pass

        # Check if interrupted at human_review
        graph_state = graph.get_state(config)
        while graph_state.next and "human_review" in str(graph_state.next):
            if q:
                response = await asyncio.wait_for(q.get(), timeout=600)
                if response["type"] == "approval":
                    graph.update_state(
                        config,
                        {
                            "approved": response["approved"],
                            "approval_feedback": response.get("feedback"),
                        },
                    )
                    async for event in graph.astream(None, config):
                        pass
                    graph_state = graph.get_state(config)

        update_session(launch_id, "completed", graph.get_state(config).values)

    except asyncio.TimeoutError:
        await websocket.send_text(json.dumps({
            "type": "error",
            "data": "Session timed out waiting for input",
        }))
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "data": str(e)}))
        update_session(launch_id, "failed", {})


# ─── X OAuth ─────────────────────────────────────────────────────────────────

@app.get("/auth/x/init")
async def x_oauth_init():
    token_data = get_request_token()
    # Store request token secret
    _oauth_request_tokens[token_data["request_token"]] = token_data["request_token_secret"]
    return {"redirect_url": token_data["redirect_url"]}


@app.get("/auth/x/callback")
async def x_oauth_callback(oauth_token: str, oauth_verifier: str):
    request_token_secret = _oauth_request_tokens.pop(oauth_token, None)
    if not request_token_secret:
        raise HTTPException(status_code=400, detail="Invalid OAuth token")

    try:
        token_data = exchange_verifier_for_tokens(
            request_token=oauth_token,
            request_token_secret=request_token_secret,
            oauth_verifier=oauth_verifier,
        )
        save_x_tokens(
            user_id="demo_user",  # TODO: real auth
            screen_name=token_data["screen_name"],
            access_token=token_data["access_token"],
            access_token_secret=token_data["access_token_secret"],
        )
        return {"success": True, "screen_name": token_data["screen_name"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Extension WebSocket ──────────────────────────────────────────────────────

@app.websocket("/ws/extension/{launch_id}")
async def extension_websocket(websocket: WebSocket, launch_id: str):
    """Chrome extension connects here to receive browser-use commands."""
    await websocket.accept()
    register_extension(launch_id, websocket)

    try:
        while True:
            msg_text = await websocket.receive_text()
            msg = json.loads(msg_text)
            if msg.get("type") == "browser_result":
                await receive_browser_result(launch_id, msg["data"])
    except WebSocketDisconnect:
        pass
    finally:
        unregister_extension(launch_id)
