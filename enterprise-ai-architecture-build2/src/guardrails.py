# src/guardrails.py
import os
import time
from dataclasses import dataclass
from typing import Dict, Tuple

from fastapi import HTTPException


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class GuardrailsConfig:
    max_prompt_chars: int = _get_int_env("MAX_PROMPT_CHARS", 4000)
    max_tokens_hard_limit: int = _get_int_env("MAX_TOKENS_HARD_LIMIT", 800)
    rate_limit_per_minute: int = _get_int_env("RATE_LIMIT_PER_MINUTE", 20)


class SimpleRateLimiter:
    """
    In-memory token bucket-ish limiter (windowed counter).
    Good enough for local/dev + single instance.
    For production, replace with Redis or API gateway rate limiting.
    """
    def __init__(self, per_minute: int):
        self.per_minute = max(1, per_minute)
        self._window: Dict[str, Tuple[int, float]] = {}  # key -> (count, window_start)

    def check(self, key: str) -> None:
        now = time.time()
        count, start = self._window.get(key, (0, now))
        if now - start >= 60:
            # reset window
            count, start = 0, now

        count += 1
        self._window[key] = (count, start)

        if count > self.per_minute:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again soon.")


def enforce_guardrails(prompt: str, max_tokens: int, cfg: GuardrailsConfig) -> int:
    if not prompt or not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required.")

    if len(prompt) > cfg.max_prompt_chars:
        raise HTTPException(
            status_code=400,
            detail=f"Prompt too long. Max {cfg.max_prompt_chars} characters.",
        )

    # Clamp tokens
    safe_tokens = min(max_tokens, cfg.max_tokens_hard_limit)
    safe_tokens = max(1, safe_tokens)
    return safe_tokens
