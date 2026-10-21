from datetime import date, timedelta

import pytest

from bulking_app.ai import budget
from bulking_app.ai.budget import (
    AIUnavailable, BudgetExceeded, BudgetGuard, GuardedPlanner,
    ProviderUnavailable, estimate_tokens, request_key,
)


class Clock:
    def __init__(self):
        self.now = 1_000_000.0
        self.day = date(2030, 1, 1)

    def time(self):
        return self.now

    def today(self):
        return self.day


class FakePlanner:
    name = "fake"
    model = "fake-model"

    def __init__(self, error=None):
        self.calls = 0
        self.error = error

    def generate_plan(self, context):
        self.calls += 1
        if self.error:
            raise self.error
        return {"summary": "ok", "n": self.calls}


def make(clock=None, **kw):
    clock = clock or Clock()
    guard = BudgetGuard(clock=clock.time, today=clock.today, **kw)
    return clock, guard


def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcde") == 2


def test_request_key_stable_and_distinct():
    assert request_key("p", "m", {"a": 1, "b": 2}) == request_key("p", "m", {"b": 2, "a": 1})
    assert request_key("p", "m", {"a": 1}) != request_key("p", "m", {"a": 2})
    assert request_key("p", "m", {"a": 1}) != request_key("p", "m2", {"a": 1})
    assert request_key("p", "m", {"a": 1}) != request_key("q", "m", {"a": 1})


def test_cache_hit_avoids_second_call_and_usage():
    _, guard = make(max_calls_per_day=5, max_tokens_per_day=10_000, cache_ttl_seconds=60)
    planner = FakePlanner()
    gp = GuardedPlanner(planner, guard)
    first = gp.generate_plan({"x": 1})
    second = gp.generate_plan({"x": 1})
    assert first == second
    assert planner.calls == 1
    assert guard.usage()["calls"] == 1


def test_cache_returns_copy():
    _, guard = make(cache_ttl_seconds=60)
    gp = GuardedPlanner(FakePlanner(), guard)
    gp.generate_plan({"x": 1})["summary"] = "mutated"
    assert gp.generate_plan({"x": 1})["summary"] == "ok"


def test_cache_miss_on_different_context():
    _, guard = make(cache_ttl_seconds=60)
    planner = FakePlanner()
    gp = GuardedPlanner(planner, guard)
    gp.generate_plan({"x": 1})
    gp.generate_plan({"x": 2})
    assert planner.calls == 2


def test_cache_ttl_expiry():
    clock, guard = make(cache_ttl_seconds=60)
    planner = FakePlanner()
    gp = GuardedPlanner(planner, guard)
    gp.generate_plan({"x": 1})
    clock.now += 59
    gp.generate_plan({"x": 1})
    assert planner.calls == 1
    clock.now += 2
    gp.generate_plan({"x": 1})
    assert planner.calls == 2


def test_call_cap():
    _, guard = make(max_calls_per_day=2, max_tokens_per_day=10_000, cache_ttl_seconds=60)
    planner = FakePlanner()
    gp = GuardedPlanner(planner, guard)
    gp.generate_plan({"x": 1})
    gp.generate_plan({"x": 2})
    with pytest.raises(BudgetExceeded):
        gp.generate_plan({"x": 3})
    assert planner.calls == 2
    # Cached request still served when over the cap.
    assert gp.generate_plan({"x": 1})["summary"] == "ok"


def test_token_cap():
    _, guard = make(max_calls_per_day=100, max_tokens_per_day=1, cache_ttl_seconds=60)
    planner = FakePlanner()
    with pytest.raises(BudgetExceeded):
        GuardedPlanner(planner, guard).generate_plan({"x": 1})
    assert planner.calls == 0
    assert guard.usage()["calls"] == 0


def test_token_usage_is_tracked_as_estimate():
    _, guard = make(max_calls_per_day=100, max_tokens_per_day=100_000)
    GuardedPlanner(FakePlanner(), guard).generate_plan({"x": 1})
    usage = guard.usage()
    assert usage["estimated_tokens"] > 0
    assert usage["tokens_are_estimates"] is True


def test_daily_reset_with_injected_clock():
    clock, guard = make(max_calls_per_day=1, cache_ttl_seconds=0)
    planner = FakePlanner()
    gp = GuardedPlanner(planner, guard)
    gp.generate_plan({"x": 1})
    with pytest.raises(BudgetExceeded):
        gp.generate_plan({"x": 2})
    clock.day += timedelta(days=1)
    assert guard.usage()["calls"] == 0
    gp.generate_plan({"x": 2})
    assert planner.calls == 2


def test_manual_reset():
    _, guard = make(max_calls_per_day=1, cache_ttl_seconds=60)
    planner = FakePlanner()
    gp = GuardedPlanner(planner, guard)
    gp.generate_plan({"x": 1})
    guard.reset()
    assert guard.usage()["calls"] == 0
    gp.generate_plan({"x": 1})  # cache cleared too
    assert planner.calls == 2


def test_provider_error_becomes_provider_unavailable_and_counts():
    _, guard = make(max_calls_per_day=5, cache_ttl_seconds=60)
    planner = FakePlanner(error=RuntimeError("boom secret-ish detail"))
    gp = GuardedPlanner(planner, guard)
    with pytest.raises(ProviderUnavailable) as info:
        gp.generate_plan({"x": 1})
    assert "boom" not in str(info.value)
    assert isinstance(info.value, AIUnavailable)
    assert guard.usage()["calls"] == 1


def test_errors_are_not_cached():
    _, guard = make(cache_ttl_seconds=60)
    planner = FakePlanner(error=ValueError("bad"))
    gp = GuardedPlanner(planner, guard)
    for _ in range(2):
        with pytest.raises(ProviderUnavailable):
            gp.generate_plan({"x": 1})
    assert planner.calls == 2
    planner.error = None
    assert gp.generate_plan({"x": 1})["summary"] == "ok"


def test_pass_through_name_and_result():
    _, guard = make()
    planner = FakePlanner()
    gp = GuardedPlanner(planner, guard)
    assert gp.name == "fake"
    assert gp.generate_plan({"x": 1}) == {"summary": "ok", "n": 1}


def test_env_configuration(monkeypatch):
    monkeypatch.setenv("AI_MAX_CALLS_PER_DAY", "3")
    monkeypatch.setenv("AI_MAX_TOKENS_PER_DAY", "77")
    monkeypatch.setenv("AI_CACHE_TTL_SECONDS", "5")
    guard = BudgetGuard()
    assert (guard.max_calls, guard.max_tokens, guard.ttl) == (3, 77, 5)


def test_env_defaults_when_blank_or_invalid(monkeypatch):
    monkeypatch.setenv("AI_MAX_CALLS_PER_DAY", "")
    monkeypatch.setenv("AI_MAX_TOKENS_PER_DAY", "abc")
    monkeypatch.setenv("AI_CACHE_TTL_SECONDS", "-4")
    guard = BudgetGuard()
    assert guard.max_calls == budget.DEFAULT_MAX_CALLS_PER_DAY
    assert guard.max_tokens == budget.DEFAULT_MAX_TOKENS_PER_DAY
    assert guard.ttl == budget.DEFAULT_CACHE_TTL_SECONDS


def test_default_guard_is_shared_and_resettable():
    budget.reset_default_guard()
    first = budget.get_default_guard()
    assert budget.get_default_guard() is first
    budget.reset_default_guard()
    assert budget.get_default_guard() is not first
    budget.reset_default_guard()


def test_get_planner_wraps_without_network(monkeypatch):
    from bulking_app.ai import factory
    fake = FakePlanner()
    monkeypatch.setattr(factory, "_build_planner", lambda provider: fake)
    assert isinstance(factory.get_planner("anything"), GuardedPlanner)
    assert factory.get_planner("anything", guarded=False) is fake


def test_get_planner_unknown_provider_still_raises():
    from bulking_app.ai.factory import get_planner
    with pytest.raises(ValueError):
        get_planner("unknown")
