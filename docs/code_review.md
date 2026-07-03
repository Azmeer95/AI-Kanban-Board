# Code Review: Project Management MVP

## Overview

This is a Kanban board app with a Next.js frontend, Python FastAPI backend, SQLite database, and an AI assistant powered by OpenRouter. The project is well organized with a clean structure, but there are several issues to address before moving forward.

---

## What Works Well

- **Clean project structure.** Code is separated into frontend/, backend/, scripts/, and docs/ directories. Easy to navigate.
- **Consistent design system.** The color scheme (yellow, blue, purple, navy, gray) is applied uniformly through CSS custom properties.
- **Good test coverage.** There are unit tests for the drag-and-drop logic, component tests for the board, backend API tests, storage tests, and Playwright end-to-end tests.
- **Smooth drag and drop.** The card movement logic is cleanly separated from the UI and well tested.
- **Docker-ready.** Multi-stage Docker build with compose support for easy deployment.
- **TypeScript types on the frontend.** The card, column, and board data structures have proper type definitions.
- **Good offline fallback.** If the backend isn't reachable, the board still loads with example data so the UI isn't broken.

---

## Issues That Need Fixing

### 1. Duplicate import (backend/app/main.py, lines 4 and 17)

`import os` appears twice. The second one on line 17 is unnecessary and should be removed.

### 2. Column rename resets unexpectedly (frontend/src/components/KanbanColumn.tsx, lines 48-51)

When renaming a column, every keystroke saves the new name to the backend. On blur, the input resets to the original title from the parent component. If the parent has already saved the new name, this works fine, but if another part of the app (like the AI assistant) changes the column title, the input won't update to reflect it.

### 3. Board refreshes twice after AI chat (frontend/src/components/AiChat.tsx, line 47)

After the AI responds, `onBoardRefresh()` fetches the board and updates it. Then `fetchBoard()` is called again immediately, fetching the same data a second time. This is wasteful and could slow things down.

### 4. Hardcoded API URL in AI chat (frontend/src/components/AiChat.tsx, line 29)

The AI chat component has `http://localhost:8000/api/ai/chat` hardcoded. The rest of the app uses a configurable `API_BASE_URL` from `api.ts`. This will break if the app is deployed to a different address.

### 5. Incompatible drag-and-drop library versions (frontend/package.json, lines 17-19)

`@dnd-kit/sortable` is version 10, but `@dnd-kit/core` is version 6. These are not compatible with each other. This could cause drag-and-drop to fail silently or behave oddly.

### 6. Temporary test folders are left behind

The storage test (`backend/tests/test_storage.py`) creates folders called `kanban-test-*` in the project root and doesn't always clean them up. There are currently 7 of these folders cluttering the project.

### 7. Weak login security

The login uses the credentials "user" / "password" hardcoded in the backend. The token is just a JSON string, not a proper signed JWT. Acceptable for a local MVP but worth noting.

### 8. CORS is wide open (backend/app/main.py, line 24)

The backend allows requests from any website (`*`). This is fine for local development but would be a security risk in a real deployment.

### 9. AI cannot actually modify the board (backend/app/main.py, lines 118-159)

The AI chat endpoint sends the board data to the AI and returns the AI's text reply, but it never changes the board based on what the AI says. The plan calls for the AI to be able to add, move, or edit cards, but this feature is not yet built.

### 10. README is slightly wrong (README.md, line 6)

It says the data uses "local JSON storage" but the project actually uses SQLite.

### 11. Backend test depends on frontend build (backend/tests/test_api.py, lines 17-20)

One test checks that the root URL returns the frontend HTML. This test will fail if the frontend hasn't been built first, which is a fragile setup.

### 12. Silent failures when saving board (frontend/src/components/KanbanBoard.tsx)

If saving the board to the backend fails (network issue, server error), the error is silently ignored. The UI looks like everything saved fine, but the data is lost. Users will have no way to know something went wrong.

### 13. Uses pip instead of uv (Dockerfile, scripts)

The project instructions say to use `uv` as the Python package manager, but the Dockerfile and start scripts use `pip` instead.

### 14. Test files included in Docker image (Dockerfile, line 25)

The Docker production image copies the `frontend/src` folder, which includes test files that are not needed at runtime. This makes the image larger than necessary.

---

## Summary

The project is on the right track with a solid foundation. The main priorities should be:

1. Fix the `@dnd-kit` version mismatch since this could cause drag-and-drop bugs
2. Add error handling so users know when their changes aren't saved
3. Clean up the hardcoded AI chat URL and double board refresh
4. Build the AI board-modification feature if the plan calls for it
5. Switch to `uv` to match the project instructions
6. Update the README to describe the actual database
7. Clean up the stale test folders
