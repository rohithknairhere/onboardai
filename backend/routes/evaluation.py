"""Endpoints behind the Evaluation Lab page used in the final review demo."""
import logging
import tempfile
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from evaluation import runner

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/eval")


class MessageProbe(BaseModel):
    message: str


class RetrievalProbe(BaseModel):
    question: str
    emp_id: str = "emp_1"


@router.get("/routing")
def routing():
    return runner.run_routing()


@router.get("/retrieval")
def retrieval():
    return runner.run_retrieval()


@router.get("/answers")
def answers():
    return runner.answers_summary()


@router.post("/answers/{case_id}")
def answer(case_id: str):
    try:
        return runner.answer_case(case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown case")


@router.get("/documents")
def documents():
    return runner.run_documents()


@router.get("/documents/{filename}")
def document_file(filename: str):
    """Download one generated test document so it can be uploaded by hand."""
    path = (runner.DEMO_COPY_DIR / filename).resolve()
    if path.parent != runner.DEMO_COPY_DIR.resolve() or not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=path.name)


@router.post("/probe/message")
def probe_message(body: MessageProbe):
    return runner.probe_message(body.message)


@router.post("/probe/retrieval")
def probe_retrieval(body: RetrievalProbe):
    return runner.probe_retrieval(body.question, body.emp_id)


@router.post("/probe/document")
def probe_document(
    file: UploadFile = File(...),
    requirement: Optional[str] = Form(None),
    employee_name: Optional[str] = Form(None),
):
    """Analyse any uploaded file without attaching it to an employee."""
    from ml import pipeline

    suffix = Path(file.filename or "upload").suffix.lower()
    content_type = file.content_type or ("application/pdf" if suffix == ".pdf" else "image/png")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"probe{suffix or '.bin'}"
        path.write_bytes(file.file.read(10 * 1024 * 1024))
        started = time.perf_counter()
        a = pipeline.analyse(path, content_type, requirement_name=requirement or None,
                             employee_name=employee_name or None)
    a.pop("text", None)
    a["ms"] = round((time.perf_counter() - started) * 1000, 1)
    return a


@router.post("/warmup")
def warmup():
    """Load the language model into memory before the audience is watching.

    The first request after Ollama starts can take minutes while the model
    loads; every request after that takes seconds.
    """
    import llm_provider

    started = time.perf_counter()
    try:
        llm_provider.get_llm(temperature=0).invoke("Reply with the single word: ready")
        ok, detail = True, "ready"
    except Exception as exc:
        ok, detail = False, f"{type(exc).__name__}: {exc}"
    return {"ok": ok, "detail": detail, "seconds": round(time.perf_counter() - started, 1),
            "provider": llm_provider.active_provider(), "model": llm_provider.active_model()}


@router.post("/reset-demo")
def reset_demo():
    """Put every employee back to the starting state and forget all chats."""
    import seed
    from agents import chatbot

    seed.seed()
    chatbot.reset_memory()
    return {"ok": True}
