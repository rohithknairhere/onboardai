from pathlib import Path

from fastapi import FastAPI
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
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(evaluation.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to OnboardAI API"}

@app.get("/api/health")
def health():
    return {"status": "ok", "llm": llm_provider.health()}
