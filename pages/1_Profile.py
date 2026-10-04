"""View and edit the single user's profile."""

import streamlit as st

from bulking_app.repositories.user_profile import (
    PROFILE_FIELDS, get_user_profile, upsert_user_profile,
)

st.set_page_config(page_title="Profile | Bulk App", page_icon="👤", layout="centered")
st.title("User Profile")
st.caption("Your saved profile is the source of truth used to build future AI requests.")

try:
    profile = get_user_profile()
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()

profile = profile or {}
with st.form("user_profile_form"):
    left, right = st.columns(2)
    with left:
        age = st.number_input("Age", 13, 100, int(profile.get("age", 21)), 1)
        height_cm = st.number_input("Height (cm)", 100.0, 250.0, float(profile.get("height_cm", 170)), 0.5)
        target_weight_kg = st.number_input("Target weight (kg)", 25.0, 350.0,
                                           float(profile.get("target_weight_kg", 60)), 0.5)
        diet_type = st.text_input("Diet type", str(profile.get("diet_type", "")),
                                  placeholder="e.g. vegetarian with eggs")
        diet_philosophy = st.text_input("Diet philosophy", str(profile.get("diet_philosophy", "")),
                                        placeholder="e.g. easy adherence")
    with right:
        calorie_strategy = st.text_input("Calorie strategy", str(profile.get("calorie_strategy", "")),
                                         placeholder="e.g. gradual surplus")
        cuisine_preference = st.text_input("Cuisine preference", str(profile.get("cuisine_preference", "")),
                                           placeholder="e.g. Indian")
        regional_context = st.text_input("Regional context", str(profile.get("regional_context", "")),
                                         placeholder="City or region")
        cooking_complexity = st.text_input("Cooking complexity", str(profile.get("cooking_complexity", "")),
                                           placeholder="e.g. minimal")
        meals_per_day = st.number_input("Meals per day", 1, 10,
                                        int(profile.get("meals_per_day", 5)), 1)
    submitted = st.form_submit_button("Save Profile", type="primary")

if submitted:
    values = dict(zip(PROFILE_FIELDS, (age, height_cm, target_weight_kg, diet_type,
                                      diet_philosophy, calorie_strategy, cuisine_preference,
                                      regional_context, cooking_complexity, meals_per_day)))
    try:
        upsert_user_profile(values)
        st.success("Profile saved.")
        st.rerun()
    except (RuntimeError, ValueError) as exc:
        st.error(str(exc))
