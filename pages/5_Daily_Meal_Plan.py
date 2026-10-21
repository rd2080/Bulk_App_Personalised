"""Create and maintain a saved meal plan for each date."""

from __future__ import annotations

from datetime import date

import streamlit as st

from bulking_app.repositories.meal_plan import MEAL_TYPES, delete_meal, list_meals, save_meal

st.set_page_config(page_title="Daily Meal Plan | Bulk App", page_icon="🍽️", layout="wide")
st.title("Daily Meal Plan")
st.caption("Save, review, and update the meals you plan to eat each day.")
plan_date = st.date_input("Plan date", value=date.today(), key="meal_plan_date")

try:
    meals = list_meals(plan_date)
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()

st.subheader(f"Plan for {plan_date.isoformat()}")

with st.expander("Add a meal", expanded=not meals):
    with st.form("add_meal_form", clear_on_submit=True):
        meal_type = st.selectbox("Meal", MEAL_TYPES)
        meal_name = st.text_input("Meal name", placeholder="Paneer bhurji with roti")
        description = st.text_area("Details (optional)", placeholder="Portion size, preparation notes, etc.")
        if st.form_submit_button("Add meal", type="primary"):
            try:
                save_meal(plan_date=plan_date, meal_type=meal_type,
                          meal_name=meal_name, description=description)
                st.success("Meal added to this day's plan.")
                st.rerun()
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))

if not meals:
    st.info("No meals saved for this date yet.")

for meal in meals:
    with st.container(border=True):
        left, action = st.columns([6, 1])
        left.markdown(f"**{meal['meal_type']} — {meal['meal_name']}**")
        if meal["description"]:
            left.write(meal["description"])
        if action.button("Edit", key=f"edit_meal_{meal['id']}"):
            st.session_state["editing_meal_id"] = meal["id"]
            st.rerun()
        if st.session_state.get("editing_meal_id") == meal["id"]:
            with st.form(f"edit_meal_form_{meal['id']}"):
                types_index = MEAL_TYPES.index(meal["meal_type"])
                new_type = st.selectbox("Meal", MEAL_TYPES, index=types_index)
                new_name = st.text_input("Meal name", value=meal["meal_name"])
                new_description = st.text_area("Details (optional)", value=meal["description"])
                save_col, cancel_col, delete_col = st.columns(3)
                if save_col.form_submit_button("Save changes", type="primary"):
                    try:
                        save_meal(plan_date=plan_date, meal_id=meal["id"], meal_type=new_type,
                                  meal_name=new_name, description=new_description)
                        st.session_state.pop("editing_meal_id", None)
                        st.rerun()
                    except (RuntimeError, ValueError) as exc:
                        st.error(str(exc))
                if cancel_col.form_submit_button("Cancel"):
                    st.session_state.pop("editing_meal_id", None)
                    st.rerun()
                if delete_col.form_submit_button("Remove meal"):
                    delete_meal(plan_date=plan_date, meal_id=meal["id"])
                    st.session_state.pop("editing_meal_id", None)
                    st.rerun()
