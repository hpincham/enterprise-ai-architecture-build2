# src/main.py
import hashlib
import logging
import os
import time
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from openai import AuthenticationError, PermissionDeniedError, RateLimitError, APIError

from src.logging_config import configure_logging
from src.openai_client import get_aoai_client
from src.guardrails import GuardrailsConfig, SimpleRateLimiter, enforce_guardrails
from src.retry import with_backoff

load_dotenv()
configure_logging()
log = logging.getLogger("enterprise-ai-gateway")

app = FastAPI(title="Enterprise AI Gateway (Build 2)")

cfg = GuardrailsConfig()
rate_limiter = SimpleRateLimiter(cfg.rate_limit_per_minute)


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1)
    max_tokens: int = Field(default=200, ge=1, le=800)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.perf_counter()

    try:
        response = await call_next(request)
        return response
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)
        # Avoid logging bodies; only metadata
        log.info(
            "request_complete",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": getattr(locals().get("response", None), "status_code", None),
                "latency_ms": latency_ms,
            },
        )


@app.get("/health")
def health():
    return {"status": "ok", "build": 2}


def _client_key_from_request(req: Request) -> str:
    """
    Build 2: we don't have Entra caller identity yet.
    Use IP + User-Agent hash as a coarse key.
    In Build 3/4 we replace this with oid/sub from JWT.
    """
    ip = (req.client.host if req.client else "unknown").strip()
    ua = (req.headers.get("user-agent") or "unknown").strip()
    raw = f"{ip}|{ua}".encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()[:16]


@app.post("/chat")
def chat(req: Request, body: ChatRequest):
    request_id = req.headers.get("x-request-id") or str(uuid.uuid4())
    client_key = _client_key_from_request(req)

    # Rate limit (before calling AOAI)
    rate_limiter.check(client_key)

    # Guardrails
    safe_tokens = enforce_guardrails(body.prompt, body.max_tokens, cfg)

    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if not deployment:
        raise HTTPException(status_code=500, detail="AZURE_OPENAI_DEPLOYMENT not set")

    client = get_aoai_client()

    start = time.perf_counter()

    try:
        def _call():
            return client.chat.completions.create(
                model=deployment,  # Azure deployment name
                messages=[{"role": "user", "content": body.prompt}],
                max_tokens=safe_tokens,
            )

        resp = with_backoff(_call, max_retries=3)
        latency_ms = int((time.perf_counter() - start) * 1000)

        # Log metadata only (no prompt/response)
        log.info(
            "chat_complete",
            extra={
                "request_id": request_id,
                "client_key": client_key,
                "latency_ms": latency_ms,
                "path": "/chat",
                "method": "POST",
                "status_code": 200,
            },
        )

        return {"response": resp.choices[0].message.content, "model": deployment}

    except (AuthenticationError, PermissionDeniedError) as e:
        # Auth to Azure OpenAI failed (not caller auth)
        log.warning(
            "aoai_auth_failed",
            extra={"request_id": request_id, "client_key": client_key, "status_code": 502},
        )
        raise HTTPException(status_code=502, detail="Azure OpenAI authentication/authorization failed.") from e

    except RateLimitError as e:
        log.warning(
            "aoai_rate_limited",
            extra={"request_id": request_id, "client_key": client_key, "status_code": 429},
        )
        raise HTTPException(status_code=429, detail="Upstream rate limit. Try again soon.") from e

    except APIError as e:
        # Upstream error; keep message generic
        log.error(
            "aoai_api_error",
            extra={"request_id": request_id, "client_key": client_key, "status_code": 502},
            exc_info=True,
        )
        raise HTTPException(status_code=502, detail="Azure OpenAI error.") from e

    except HTTPException:
        raise

    except Exception as e:
        log.error(
            "unexpected_error",
            extra={"request_id": request_id, "client_key": client_key, "status_code": 500},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error.") from e
