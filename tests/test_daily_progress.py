"""Daily progress service tests (synthetic logs, no database)."""

from bulking_app.services.daily_progress import daily_progress, summarise


def log(kcal, protein, source="user_entered"):
    return {"calories_kcal": kcal, "protein_g": protein, "nutrition_source": source}


def test_totals_and_target():
    r = summarise([log(300, 20), log(200.5, 10)], target_kcal=1000, target_protein_g=60)
    assert r["calories"]["eaten"] == 500.5
    assert r["calories"]["remaining"] == 499.5
    assert r["protein"]["percent"] == 50.0
    assert not r["incomplete"]


def test_unknown_not_zero_and_incomplete():
    r = summarise([log(300, 20), log(None, None, "unknown")], target_kcal=1000)
    assert r["incomplete"] and r["note"]
    assert r["calories"]["eaten"] == 300 and r["calories"]["unknown_items"] == 1


def test_all_unknown_eaten_is_none():
    r = summarise([log(None, None, "unknown")])
    assert r["calories"]["eaten"] is None and r["protein"]["eaten"] is None


def test_partial_unknown_protein():
    r = summarise([log(300, None, "user_entered")])
    assert r["protein"]["eaten"] is None and r["incomplete"]


def test_no_target_and_empty_day():
    r = summarise([])
    assert r["calories"]["target"] is None and r["calories"]["eaten"] is None
    assert not r["incomplete"]


def test_over_target_remaining_zero():
    r = summarise([log(1200, 10)], target_kcal=1000)
    assert r["calories"]["remaining"] == 0 and r["calories"]["percent"] == 120.0


def test_uses_only_injected_logs_not_plans():
    seen = []
    r = daily_progress("2026-01-01", target_kcal=500,
                       list_logs=lambda d: seen.append(d) or [log(250, 5)])
    assert seen == ["2026-01-01"] and r["calories"]["percent"] == 50.0


def test_estimates_flagged():
    assert summarise([log(100, 5, "estimate")])["includes_estimates"]
