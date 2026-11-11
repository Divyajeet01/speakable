"""Speakable - TTS text normalization API.

Run locally:  uvicorn app:app --reload
Docs:         http://127.0.0.1:8000/docs
"""
import os
import time

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from speakable import __version__, normalize

# RapidAPI injects this header on every proxied call. Set the env var to the
# value from your RapidAPI dashboard to reject traffic that bypasses billing.
PROXY_SECRET = os.getenv("RAPIDAPI_PROXY_SECRET", "")
MAX_CHARS = int(os.getenv("MAX_CHARS", "20000"))
MAX_BATCH = int(os.getenv("MAX_BATCH", "100"))

app = FastAPI(
    title="Speakable",
    version=__version__,
    description=(
        "Turn LLM output into text a TTS engine speaks correctly.\n\n"
        "Strips markdown and emoji, and rewrites currency, dates, times, "
        "phone numbers, percentages, ordinals, units and abbreviations into "
        "spoken form. Built for voice agents."
    ),
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])


class NormalizeRequest(BaseModel):
    text: str = Field(..., examples=["**Total: $1,234.56** due 2026-11-11."])
    spell_acronyms: bool = Field(
        False, description="Spell out acronyms: 'API' -> 'A P I'.")
    strip_emoji: bool = Field(True, description="Remove emoji entirely.")


class BatchRequest(BaseModel):
    texts: list[str] = Field(..., examples=[["Call $5", "Due 2026-01-05"]])
    spell_acronyms: bool = False
    strip_emoji: bool = True


class NormalizeResponse(BaseModel):
    text: str
    original: str
    chars_in: int
    chars_out: int
    took_ms: float


def _check(secret):
    if PROXY_SECRET and secret != PROXY_SECRET:
        raise HTTPException(403, "Direct access is not permitted.")


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "version": __version__}


@app.post("/normalize", response_model=NormalizeResponse, tags=["normalize"])
def normalize_one(
    body: NormalizeRequest,
    x_rapidapi_proxy_secret: str = Header("", alias="X-RapidAPI-Proxy-Secret"),
):
    """Normalize a single string for text-to-speech."""
    _check(x_rapidapi_proxy_secret)
    if len(body.text) > MAX_CHARS:
        raise HTTPException(413, "text exceeds %d characters" % MAX_CHARS)
    started = time.perf_counter()
    out = normalize(body.text, body.spell_acronyms, body.strip_emoji)
    return NormalizeResponse(
        text=out,
        original=body.text,
        chars_in=len(body.text),
        chars_out=len(out),
        took_ms=round((time.perf_counter() - started) * 1000, 3),
    )


@app.post("/normalize/batch", tags=["normalize"])
def normalize_many(
    body: BatchRequest,
    x_rapidapi_proxy_secret: str = Header("", alias="X-RapidAPI-Proxy-Secret"),
):
    """Normalize up to MAX_BATCH strings in one call."""
    _check(x_rapidapi_proxy_secret)
    if len(body.texts) > MAX_BATCH:
        raise HTTPException(413, "batch exceeds %d items" % MAX_BATCH)
    if sum(len(t) for t in body.texts) > MAX_CHARS:
        raise HTTPException(413, "batch exceeds %d characters" % MAX_CHARS)
    started = time.perf_counter()
    results = [normalize(t, body.spell_acronyms, body.strip_emoji)
               for t in body.texts]
    return {
        "results": results,
        "count": len(results),
        "took_ms": round((time.perf_counter() - started) * 1000, 3),
    }
