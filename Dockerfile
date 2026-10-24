# Web deploy (no seed path): build frontend, serve it + API from Flask via gunicorn

FROM node:22-slim AS frontend
WORKDIR /app
COPY rubin.txt ./
COPY frontend/package*.json frontend/
RUN npm ci --prefix frontend
COPY frontend frontend
# empty API URL = same origin as Flask
RUN VITE_API_URL= npm run build --prefix frontend

FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend backend
COPY prompt_guides/stable_audio_prompt_guide.md prompt_guides/
COPY --from=frontend /app/frontend/dist frontend/dist
ENV ENABLE_SEED=0 PORT=8080 PYTHONUNBUFFERED=1
# long timeout: generation polls Stability for a while
CMD exec gunicorn --chdir backend --bind :$PORT --workers 1 --threads 8 --timeout 300 app:app
