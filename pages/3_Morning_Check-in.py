"""Objective daily morning check-in page."""

from datetime import date

import streamlit as st

from bulking_app.repositories.morning_checkin import (
    get_morning_checkin,
    recent_morning_checkins,
    save_morning_checkin,
)

st.set_page_config(page_title="Morning Check-in | Bulk App", page_icon="🌅", layout="centered")
st.title("Morning Check-in")
st.caption("Record today's weight, sleep, and soreness. Notes are optional.")

checkin_date = st.date_input("Check-in date", value=date.today())
existing = None
try:
    existing = get_morning_checkin(checkin_date)
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()

with st.form("morning_checkin_form"):
    weight = st.number_input(
        "Weight (kg)", min_value=25.0, max_value=350.0,
        value=float(existing["weight_kg"]) if existing else 70.0, step=0.1,
    )
    sleep = st.number_input(
        "Sleep (hours)", min_value=0.0, max_value=24.0,
        value=float(existing["sleep_hours"]) if existing else 8.0, step=0.5,
    )
    soreness = st.slider(
        "Soreness (1 = none, 10 = very sore)", min_value=1, max_value=10,
        value=int(existing["soreness_level"]) if existing else 1,
    )
    notes = st.text_area("Notes (optional)", value=existing["daily_notes"] if existing else "")
    submitted = st.form_submit_button("Save check-in", type="primary")

if submitted:
    try:
        save_morning_checkin(
            checkin_date=checkin_date, weight_kg=weight, sleep_hours=sleep,
            soreness_level=soreness, daily_notes=notes,
        )
        st.success(f"Check-in saved for {checkin_date.isoformat()}.")
        st.rerun()
    except (RuntimeError, ValueError) as exc:
        st.error(str(exc))

st.subheader("Recent check-ins")
try:
    history = recent_morning_checkins()
    if history:
        st.dataframe(history, use_container_width=True, hide_index=True)
    else:
        st.info("No check-ins saved yet.")
except RuntimeError as exc:
    st.error(str(exc))
