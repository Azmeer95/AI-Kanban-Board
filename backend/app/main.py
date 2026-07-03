from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.app.storage import BoardStore

security = HTTPBearer(auto_error=False)

app = FastAPI(title="Kanban API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


class BoardPayload(BaseModel):
    columns: list[dict[str, Any]]
    cards: dict[str, dict[str, Any]]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthenticatedUser(BaseModel):
    username: str


class AiRequest(BaseModel):
    message: str


store = BoardStore()


def _frontend_index_path() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "..", "frontend", ".next", "server", "app", "index.html")


def create_app() -> FastAPI:
    return app


def _create_token(username: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=8)
    payload = {"sub": username, "exp": int(expires_at.timestamp())}
    return json.dumps(payload)


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> AuthenticatedUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    try:
        payload = json.loads(credentials.credentials)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized") from exc

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    return AuthenticatedUser(username=username)


@app.get("/")
def serve_frontend() -> FileResponse:
    index_path = _frontend_index_path()
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Frontend build not found")


@app.post("/api/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    if payload.username == "user" and payload.password == "password":
        return TokenResponse(access_token=_create_token(payload.username))

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@app.get("/api/board")
def get_board(user: AuthenticatedUser = Depends(get_current_user)) -> dict[str, Any]:
    return store.get_board(user.username)


@app.put("/api/board")
def update_board(payload: BoardPayload, user: AuthenticatedUser = Depends(get_current_user)) -> dict[str, Any]:
    return store.save_board(user.username, payload.model_dump())


@app.get("/api/ai/health")
def ai_health() -> dict[str, str]:
    return {"status": "ok"}


def _create_card_id() -> str:
    random_part = os.urandom(4).hex()
    time_part = hex(int(datetime.now(timezone.utc).timestamp() * 1000))[2:]
    return f"card-{random_part}{time_part}"


COLUMN_IDS = ["col-backlog", "col-discovery", "col-progress", "col-review", "col-done"]


def _apply_board_actions(board: dict[str, Any], actions: list[dict[str, str]]) -> dict[str, Any]:
    columns = {col["id"]: col for col in board["columns"]}
    cards = dict(board["cards"])

    for action in actions:
        action_type = action.get("type")

        if action_type == "add_card":
            column_id = action.get("column_id")
            title = action.get("title", "").strip()
            if not column_id or column_id not in columns or not title:
                continue
            card_id = _create_card_id()
            cards[card_id] = {
                "id": card_id,
                "title": title,
                "details": action.get("details", "").strip(),
            }
            columns[column_id]["cardIds"].append(card_id)

        elif action_type == "move_card":
            card_id = action.get("card_id")
            to_column = action.get("to_column")
            if not card_id or card_id not in cards or not to_column or to_column not in columns:
                continue
            source_col = next((c for c in board["columns"] if card_id in c["cardIds"]), None)
            if source_col is None:
                continue
            source_col["cardIds"] = [cid for cid in source_col["cardIds"] if cid != card_id]
            position_str = action.get("position", "end")
            if position_str == "start":
                columns[to_column]["cardIds"].insert(0, card_id)
            elif position_str == "end":
                columns[to_column]["cardIds"].append(card_id)
            else:
                try:
                    pos = int(position_str)
                    columns[to_column]["cardIds"].insert(pos, card_id)
                except (ValueError, IndexError):
                    columns[to_column]["cardIds"].append(card_id)

        elif action_type == "edit_card":
            card_id = action.get("card_id")
            if not card_id or card_id not in cards:
                continue
            if action.get("title"):
                cards[card_id]["title"] = action["title"].strip()
            if "details" in action:
                cards[card_id]["details"] = action["details"].strip()

        elif action_type == "delete_card":
            card_id = action.get("card_id")
            if not card_id or card_id not in cards:
                continue
            cards.pop(card_id, None)
            for col in board["columns"]:
                col["cardIds"] = [cid for cid in col["cardIds"] if cid != card_id]

    board["cards"] = cards
    board["columns"] = list(columns.values())
    return board


def _parse_ai_response(content: str) -> tuple[str | None, list[dict[str, str]]]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|```\s*$", "", cleaned, flags=re.DOTALL)
        cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict) and "reply" in parsed:
            reply = parsed.get("reply", "")
            actions = parsed.get("actions", [])
            if actions and isinstance(actions, list):
                return reply, actions
            return reply, []
        if isinstance(parsed, dict) and "actions" in parsed:
            return None, parsed.get("actions", [])
    except (json.JSONDecodeError, TypeError):
        pass

    return None, []


SYSTEM_PROMPT = """You are a helpful Kanban board assistant. The user has a board with columns and cards.

You can respond in two ways:
1. A plain text message (just your reply — for conversation or when no board changes are needed)
2. A JSON object with "reply" and optionally "actions" fields (when the user asks you to modify the board)

If you want to modify the board, respond with a JSON object like this:
{
  "reply": "Your message to the user explaining what you did",
  "actions": [
    {"type": "add_card", "column_id": "col-backlog", "title": "Task title", "details": "Optional details"},
    {"type": "move_card", "card_id": "card-3", "to_column": "col-progress"},
    {"type": "edit_card", "card_id": "card-1", "title": "New title", "details": "New details"},
    {"type": "delete_card", "card_id": "card-5"}
  ]
}

Available columns with their IDs:
- Backlog: col-backlog
- Discovery: col-discovery
- In Progress: col-progress
- Review: col-review
- Done: col-done

For add_card: provide column_id, title (required), and optionally details.
For move_card: provide card_id and to_column. Optionally set position to "start", "end", or a number.
For edit_card: provide card_id and the fields to update (title, details).
For delete_card: provide card_id.

Keep replies concise and practical. Wrap your JSON in ```json ... ``` markers if you like."""


@app.post("/api/ai/chat")
def ai_chat(payload: AiRequest, user: AuthenticatedUser = Depends(get_current_user)) -> dict[str, Any]:
    board = store.get_board(user.username)
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return {
            "reply": "The AI helper is configured without an API key.",
            "board": board,
        }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT,
                        },
                        {
                            "role": "user",
                            "content": f"Board: {json.dumps(board)}\n\nUser request: {payload.message}",
                        },
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            reply, actions = _parse_ai_response(content)

            if actions:
                board = _apply_board_actions(board, actions)
                store.save_board(user.username, board)

            if reply is None:
                reply = content

            return {"reply": reply, "board": board}
    except Exception:
        return {
            "reply": "The AI helper could not be reached. Please try again shortly.",
            "board": board,
        }
