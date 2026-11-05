# One container for the hosted demo: builds the React website, then runs the
# FastAPI backend, which serves both the API (/api) and the website.

# ---- Website ----
FROM node:22-slim AS web
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html vite.config.js postcss.config.js tailwind.config.js ./
COPY public ./public
COPY src ./src
ENV VITE_API_URL=/api
RUN npm run build

# ---- Backend ----
FROM python:3.13-slim
# Run as a normal user, not root.
RUN useradd -m -u 1000 user
WORKDIR /app
COPY deploy/requirements-hosted.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user backend ./backend
COPY --chown=user --from=web /web/dist ./dist

USER user
ENV LLM_PROVIDER=groq \
    FRONTEND_DIST=/app/dist \
    PYTHONUNBUFFERED=1
WORKDIR /app/backend
EXPOSE 7860
# Hosts such as Render pass the port in PORT; 7860 when run by hand.
# A fresh demo database on every start, then the server.
CMD ["sh", "-c", "python seed.py && exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}"]
