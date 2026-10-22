"""Constraint, FK, atomicity and isolation tests on a throwaway Postgres."""

from __future__ import annotations

from datetime import date

import psycopg
import pytest

from tests.integration import conftest as c


def test_guard_refuses_production_url(monkeypatch):
    monkeypatch.setenv("SMOKE_DATABASE_URL", "postgresql://u:p@host/production")
    with pytest.raises(pytest.fail.Exception):
        c.check_url()
    monkeypatch.setenv("SMOKE_DATABASE_URL", "postgresql://u:p@ep-x.neon.tech/db")
    with pytest.raises(pytest.fail.Exception):
        c.check_url()


def test_guard_skips_without_url(monkeypatch):
    monkeypatch.delenv("SMOKE_DATABASE_URL", raising=False)
    with pytest.raises(pytest.skip.Exception):
        c.check_url()


def test_all_expected_tables_exist(conn):
    names = {r[0] for r in conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'")}
    assert {"weight_entries", "daily_checkins", "food_inventory", "user_profile",
            "recipe_library", "recipe_ingredients", "daily_meal_plans",
            "planned_meals"} <= names


@pytest.mark.parametrize("sql", [
    "INSERT INTO daily_checkins (checkin_date, soreness_level) VALUES ('2030-01-01', 11)",
    "INSERT INTO daily_checkins (checkin_date, sleep_hours) VALUES ('2030-01-01', 25)",
    "INSERT INTO daily_checkins (checkin_date, weight_kg) VALUES ('2030-01-01', 10)",
    "INSERT INTO weight_entries (entry_date, weight_kg) VALUES ('2030-01-01', 400)",
    "INSERT INTO food_inventory (food_name, availability_type) VALUES ('x', 'bogus')",
    "INSERT INTO food_inventory (food_name, availability_type, quantity) "
    "VALUES ('x', 'stock_tracked', -1)",
])
def test_check_constraints_reject_bad_rows(conn, sql):
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(sql)


def test_unique_checkin_date(conn):
    conn.execute("INSERT INTO daily_checkins (checkin_date) VALUES ('2030-01-01')")
    with pytest.raises(psycopg.errors.UniqueViolation):
        conn.execute("INSERT INTO daily_checkins (checkin_date) VALUES ('2030-01-01')")


def test_recipe_fk_restrict_and_cascade(conn):
    food = conn.execute(
        "INSERT INTO food_inventory (food_name, availability_type) "
        "VALUES ('synthetic food', 'on_demand') RETURNING id").fetchone()[0]
    recipe = conn.execute(
        """INSERT INTO recipe_library (recipe_name, recipe_type, preference_level,
               cooking_complexity, total_weight_g, calories_kcal, protein_g,
               carbohydrates_g, fat_g)
           VALUES ('synthetic recipe','meal','like','easy',100,100,10,10,1) RETURNING id"""
    ).fetchone()[0]
    conn.execute("INSERT INTO recipe_ingredients VALUES (%s,%s,1,'g')", (recipe, food))
    conn.execute("SAVEPOINT s")
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        conn.execute("DELETE FROM food_inventory WHERE id=%s", (food,))
    conn.execute("ROLLBACK TO SAVEPOINT s")
    conn.execute("DELETE FROM recipe_library WHERE id=%s", (recipe,))
    left = conn.execute("SELECT count(*) FROM recipe_ingredients WHERE recipe_id=%s",
                        (recipe,)).fetchone()[0]
    assert left == 0


def test_checkin_and_weight_rollback_together(conn):
    conn.execute("INSERT INTO daily_checkins (checkin_date, weight_kg) VALUES ('2030-02-02', 70)")
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("INSERT INTO weight_entries (entry_date, weight_kg) VALUES ('2030-02-02', 1)")
    conn.rollback()
    assert conn.execute("SELECT count(*) FROM daily_checkins WHERE checkin_date='2030-02-02'"
                        ).fetchone()[0] == 0


def test_repository_checkin_is_atomic(db_url, monkeypatch):
    from bulking_app.repositories import morning_checkin as repo

    monkeypatch.setenv("DATABASE_URL", db_url)
    day = date(2031, 3, 3)
    admin = psycopg.connect(db_url, autocommit=True)
    try:
        repo.save_morning_checkin(checkin_date=day, weight_kg=70.5, sleep_hours=7,
                                  soreness_level=3)
        assert float(repo.get_morning_checkin(day)["weight_kg"]) == 70.5
        admin.execute("""CREATE OR REPLACE FUNCTION it_fail() RETURNS trigger AS
                         $$ BEGIN RAISE EXCEPTION 'forced'; END $$ LANGUAGE plpgsql""")
        admin.execute("CREATE TRIGGER it_fail_trg BEFORE INSERT OR UPDATE ON weight_entries "
                      "FOR EACH ROW EXECUTE FUNCTION it_fail()")
        try:
            with pytest.raises(psycopg.Error):
                repo.save_morning_checkin(checkin_date=day, weight_kg=80, sleep_hours=5,
                                          soreness_level=9)
        finally:
            admin.execute("DROP TRIGGER it_fail_trg ON weight_entries")
            admin.execute("DROP FUNCTION it_fail()")
        after = repo.get_morning_checkin(day)
        assert float(after["weight_kg"]) == 70.5 and after["soreness_level"] == 3
    finally:
        admin.execute("DELETE FROM daily_checkins WHERE checkin_date=%s", (day,))
        admin.execute("DELETE FROM weight_entries WHERE entry_date=%s", (day,))
        admin.close()


def test_plan_isolation_and_cascade(conn):
    ids = []
    for d in ("2030-05-01", "2030-05-02"):
        pid = conn.execute("INSERT INTO daily_meal_plans (plan_date) VALUES (%s) RETURNING id",
                           (d,)).fetchone()[0]
        ids.append(pid)
        conn.execute("INSERT INTO planned_meals (plan_id, meal_type, meal_name, position) "
                     "VALUES (%s,'Lunch','synthetic meal',0)", (pid,))
    conn.execute("DELETE FROM daily_meal_plans WHERE id=%s", (ids[0],))
    counts = {pid: conn.execute("SELECT count(*) FROM planned_meals WHERE plan_id=%s",
                                (pid,)).fetchone()[0] for pid in ids}
    assert counts == {ids[0]: 0, ids[1]: 1}
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        conn.execute("INSERT INTO planned_meals (plan_id, meal_type, meal_name, position) "
                     "VALUES (-1,'Lunch','orphan',0)")
