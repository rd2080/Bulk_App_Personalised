"""AI budget guard: in-memory cache plus per-day call and token caps.

Limitations: counters and cache live in process memory only. They reset when
the app restarts and are not shared between processes. Token counts are rough
estimates (characters / 4), not provider-billed figures.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from datetime import date, datetime
from typing import Any, Callable

from bulking_app.ai.base import Planner, planner_prompt

DEFAULT_MAX_CALLS_PER_DAY = 20
DEFAULT_MAX_TOKENS_PER_DAY = 40_000
DEFAULT_CACHE_TTL_SECONDS = 3600


class AIUnavailable(Exception):
    """Base class: AI could not be used. Callers must fall back to manual flows."""


class BudgetExceeded(AIUnavailable):
    """A daily call or token cap would be exceeded."""


class ProviderUnavailable(AIUnavailable):
    """The provider failed or returned unusable output."""


def estimate_tokens(text: str) -> int:
    """Rough ESTIMATE of token count (len/4, rounded up)."""
    return (len(text) + 3) // 4


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 0 else default


def request_key(provider: str, model: str, context: dict[str, Any]) -> str:
    payload = json.dumps(context, sort_keys=True, default=repr)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{provider}:{model}:{digest}"


class BudgetGuard:
    def __init__(
        self,
        max_calls_per_day: int | None = None,
        max_tokens_per_day: int | None = None,
        cache_ttl_seconds: float | None = None,
        clock: Callable[[], float] = time.time,
        today: Callable[[], date] | None = None,
    ) -> None:
        self.max_calls = (max_calls_per_day if max_calls_per_day is not None
                          else _env_int("AI_MAX_CALLS_PER_DAY", DEFAULT_MAX_CALLS_PER_DAY))
        self.max_tokens = (max_tokens_per_day if max_tokens_per_day is not None
                           else _env_int("AI_MAX_TOKENS_PER_DAY", DEFAULT_MAX_TOKENS_PER_DAY))
        self.ttl = (cache_ttl_seconds if cache_ttl_seconds is not None
                    else _env_int("AI_CACHE_TTL_SECONDS", DEFAULT_CACHE_TTL_SECONDS))
        self._clock = clock
        self._today = today or (lambda: datetime.fromtimestamp(self._clock()).date())
        self._lock = threading.Lock()
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._day = self._today()
        self.calls_today = 0
        self.estimated_tokens_today = 0

    def reset(self) -> None:
        """Clear the cache and usage counters (for tests)."""
        with self._lock:
            self._cache = {}
            self._day = self._today()
            self.calls_today = 0
            self.estimated_tokens_today = 0

    def _roll_day(self) -> None:
        today = self._today()
        if today != self._day:
            self._day = today
            self.calls_today = 0
            self.estimated_tokens_today = 0

    def usage(self) -> dict[str, Any]:
        with self._lock:
            self._roll_day()
            return {"calls": self.calls_today, "max_calls": self.max_calls,
                    "estimated_tokens": self.estimated_tokens_today,
                    "max_tokens": self.max_tokens, "tokens_are_estimates": True}

    def call(self, provider: str, model: str, context: dict[str, Any],
             prompt: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        key = request_key(provider, model, context)
        with self._lock:
            now = self._clock()
            hit = self._cache.get(key)
            if hit is not None:
                if now - hit[0] < self.ttl:
                    return json.loads(json.dumps(hit[1]))
                del self._cache[key]
            self._roll_day()
            cost = estimate_tokens(prompt)
            if self.calls_today + 1 > self.max_calls:
                raise BudgetExceeded("Daily AI call limit reached.")
            if self.estimated_tokens_today + cost > self.max_tokens:
                raise BudgetExceeded("Daily AI token limit (estimated) reached.")
            # Reserve before calling so failed attempts still count.
            self.calls_today += 1
            self.estimated_tokens_today += cost
        try:
            result = fn()
        except AIUnavailable:
            raise
        except Exception as exc:  # provider/network/parse errors
            raise ProviderUnavailable(
                f"AI provider failed ({type(exc).__name__}).") from exc
        with self._lock:
            self._cache[key] = (self._clock(), json.loads(json.dumps(result)))
        return result


_default_guard: BudgetGuard | None = None


def get_default_guard() -> BudgetGuard:
    global _default_guard
    if _default_guard is None:
        _default_guard = BudgetGuard()
    return _default_guard


def reset_default_guard() -> None:
    global _default_guard
    _default_guard = None


class GuardedPlanner:
    """Planner wrapper applying cache and caps. Raises AIUnavailable subclasses."""

    def __init__(self, inner: Planner, guard: BudgetGuard | None = None) -> None:
        self.inner = inner
        self.guard = guard
        self.name = inner.name

    def generate_plan(self, context: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard or get_default_guard()
        model = str(getattr(self.inner, "model", "") or "")
        return guard.call(self.name, model, context, planner_prompt(context),
                          lambda: self.inner.generate_plan(context))
