from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.app.storage import BoardStore

import os

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
        with httpx.Client(timeout=20.0) as client:
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
                            "content": "You help a user manage a simple Kanban board. Keep replies concise and practical.",
                        },
                        {
                            "role": "user",
                            "content": f"Board: {json.dumps(board)}\nQuestion: {payload.message}",
                        },
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            reply = data["choices"][0]["message"]["content"]
            return {"reply": reply, "board": board}
    except Exception:
        return {
            "reply": "The AI helper could not be reached. Please try again shortly.",
            "board": board,
        }
