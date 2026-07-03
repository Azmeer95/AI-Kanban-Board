FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/. .
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir uv && uv pip install --system -r backend/requirements.txt

COPY backend ./backend
COPY --from=frontend-build /app/frontend/.next ./frontend/.next
COPY --from=frontend-build /app/frontend/public ./frontend/public
COPY --from=frontend-build /app/frontend/package.json ./frontend/package.json
COPY --from=frontend-build /app/frontend/next.config.ts ./frontend/next.config.ts
COPY --from=frontend-build /app/frontend/tsconfig.json ./frontend/tsconfig.json
COPY --from=frontend-build /app/frontend/postcss.config.mjs ./frontend/postcss.config.mjs
EXPOSE 8000
CMD ["sh", "-c", "cd /app && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]