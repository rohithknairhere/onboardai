import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Anchored to this file: the server is normally launched from the project root,
# where a bare load_dotenv() would look in the wrong directory and silently
# find nothing.
load_dotenv(Path(__file__).resolve().parent / ".env")

import routes.api as api
import routes.chat as chat
import routes.documents as documents
import routes.evaluation as evaluation
import llm_provider
from database import engine, Base

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="OnboardAI Backend")

# Allow CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    # Extra origins (for a separately hosted website) come from CORS_ORIGINS,
    # comma-separated. The single-container deploy needs none: same origin.
    allow_origins=["http://localhost:5173", "http://localhost:3000"] + [
        o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(evaluation.router, prefix="/api")

@app.get("/api/health")
def health():
    return {"status": "ok", "llm": llm_provider.health()}


# In the hosted build the backend also serves the website (the Vite build in
# FRONTEND_DIST), so the professor opens one address. Locally FRONTEND_DIST is
# unset and the Vite dev server serves the website as before.
FRONTEND_DIST = os.getenv("FRONTEND_DIST")
if FRONTEND_DIST and Path(FRONTEND_DIST, "index.html").is_file():
    _dist = Path(FRONTEND_DIST).resolve()

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = (_dist / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(_dist):
            return FileResponse(candidate)
        # Any other path is a page of the single-page app.
        return FileResponse(_dist / "index.html")
else:
    @app.get("/")
    def read_root():
        return {"message": "Welcome to OnboardAI API"}
