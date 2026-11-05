"""Single place where the app decides which LLM backend to talk to.

Swap providers with env vars, never by editing call sites:
    LLM_PROVIDER=ollama|gemini|groq   (default: ollama)
    LLM_MODEL=<model name>            (optional, overrides the default below)
"""
import os
import logging
import warnings

logger = logging.getLogger(__name__)

DEFAULT_MODELS = {
    "ollama": "qwen2.5:7b",
    "gemini": "gemini-3.6-flash",
    "groq": "llama-3.3-70b-versatile",
}

# Newer Gemini models pin their own sampling and warn on every single call when
# a temperature is supplied. The warning is per-request, so it drowns the logs.
warnings.filterwarnings(
    "ignore",
    message=r".*uses fixed sampling defaults.*",
    category=UserWarning,
)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def active_provider() -> str:
    return os.getenv("LLM_PROVIDER", "ollama").strip().lower()


def active_model() -> str:
    provider = active_provider()
    return os.getenv("LLM_MODEL") or DEFAULT_MODELS.get(provider, "")


def get_llm(temperature: float = 0.0, model: str | None = None):
    """Return a LangChain chat model for the configured provider.

    Imports are deferred so that an uninstalled fallback provider never breaks
    the default path.
    """
    provider = active_provider()
    model = model or active_model()

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=temperature, base_url=OLLAMA_BASE_URL)

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, temperature=temperature)

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, temperature=temperature)

    raise ValueError(
        f"Unknown LLM_PROVIDER '{provider}'. Expected one of: {', '.join(DEFAULT_MODELS)}"
    )


def health() -> dict:
    """Report whether the configured provider can actually be reached.

    Used by /api/health so the UI can show a degraded state instead of failing
    mid-conversation.
    """
    provider = active_provider()
    model = active_model()
    result = {"provider": provider, "model": model, "available": False, "detail": ""}

    try:
        if provider == "ollama":
            import httpx
            resp = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3.0)
            resp.raise_for_status()
            installed = [m["name"] for m in resp.json().get("models", [])]
            result["installed_models"] = installed
            if not any(m == model or m.startswith(f"{model}:") or m.split(":")[0] == model.split(":")[0] for m in installed):
                result["detail"] = f"Ollama is running but '{model}' is not pulled. Run: ollama pull {model}"
                return result
        elif provider == "gemini":
            key = os.getenv("GOOGLE_API_KEY", "").strip()
            if not key:
                result["detail"] = "GOOGLE_API_KEY is not set."
                return result
            import httpx
            resp = httpx.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                params={"key": key}, timeout=10.0,
            )
            if resp.status_code != 200:
                result["detail"] = f"Google API rejected the key (HTTP {resp.status_code})."
                return result
            offered = {m["name"].replace("models/", "") for m in resp.json().get("models", [])}
            if model not in offered:
                # The list endpoint also advertises retired models, so presence
                # is necessary but not sufficient; absence is still conclusive.
                result["detail"] = f"'{model}' is not offered to this key."
                return result

        else:
            if not os.getenv("GROQ_API_KEY"):
                result["detail"] = "GROQ_API_KEY is not set."
                return result

        result["available"] = True
        result["detail"] = "ready"
    except Exception as exc:
        result["detail"] = f"{type(exc).__name__}: {exc}"

    return result
