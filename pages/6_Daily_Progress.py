"""Today's calories and protein eaten versus target."""

from __future__ import annotations

from datetime import date

import streamlit as st

from bulking_app.services.daily_progress import daily_progress

st.set_page_config(page_title="Daily Progress | Bulk App", page_icon="📈", layout="wide")
st.title("Daily Progress")
st.caption("Counts only what you logged as eaten. Planned meals are never counted.")

day = st.date_input("Day", value=date.today(), key="progress_day")
st.subheader("Your targets")
st.caption("Entered by you for now; a suggested target comes later. Leave at 0 for none.")
col_k, col_p = st.columns(2)
target_kcal = col_k.number_input("Calories target (kcal)", min_value=0, step=50, key="t_kcal")
target_protein = col_p.number_input("Protein target (g)", min_value=0, step=5, key="t_protein")

try:
    result = daily_progress(day, target_kcal=target_kcal or None,
                            target_protein_g=target_protein or None)
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()


def show(label: str, unit: str, data: dict) -> None:
    eaten = "unknown" if data["eaten"] is None else f"{data['eaten']:g} {unit}"
    st.metric(label, eaten)
    if data["target"] is None:
        st.caption("No target set.")
    elif data["percent"] is None:
        st.caption(f"Target {data['target']:g} {unit}; progress unknown.")
    else:
        st.progress(min(data["percent"] / 100, 1.0))
        st.caption(f"{data['percent']:g}% of {data['target']:g} {unit}; "
                   f"{data['remaining']:g} {unit} left.")
    if data["unknown_items"]:
        st.caption(f"{data['unknown_items']} item(s) with unknown {label.lower()} not included.")


if result["item_count"] == 0:
    st.info("Nothing logged for this day yet.")
else:
    if result["incomplete"]:
        st.warning(result["note"])
    if result["includes_estimates"]:
        st.caption("Some values are estimates.")
    c1, c2 = st.columns(2)
    with c1:
        show("Calories", "kcal", result["calories"])
    with c2:
        show("Protein", "g", result["protein"])
