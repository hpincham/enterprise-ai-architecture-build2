# src/retry.py
import random
import time
from typing import Callable, TypeVar

from openai import APIError, RateLimitError

T = TypeVar("T")


def with_backoff(fn: Callable[[], T], *, max_retries: int = 3) -> T:
    """
    Retry transient errors with exponential backoff + jitter.
    Keeps it small and deterministic for Build 2.
    """
    base = 0.4  # seconds
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except RateLimitError:
            # 429
            if attempt == max_retries:
                raise
        except APIError as e:
            # Some 5xx / transient API errors come through here
            if attempt == max_retries:
                raise
            # For 4xx non-rate-limit, don't retry
            if getattr(e, "status_code", None) and 400 <= e.status_code < 500:
                raise

        sleep_s = (base * (2**attempt)) + random.uniform(0, 0.25)
        time.sleep(sleep_s)

    # Should never get here
    return fn()
