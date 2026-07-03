# Project Management MVP

This project now includes a simple local MVP with:
- a login screen using the demo credentials user / password
- a persistent Kanban board backed by a FastAPI API and SQLite database
- Docker-ready startup scripts for local development

## Run locally

1. Install Python dependencies and frontend dependencies.
2. Run the backend with `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`.
3. In a second terminal, run `npm --prefix frontend run dev`.
