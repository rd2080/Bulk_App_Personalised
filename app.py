"""Bulk App entry point."""

import streamlit as st

st.set_page_config(page_title="Bulk App", page_icon="🏋️", layout="wide")

st.title("Bulk App")
st.write("Personal bulking assistant.")
st.info("Open a page from the sidebar: Profile, Food Inventory, Morning Check-in, Voice Input or Daily Meal Plan.")

st.subheader("Current phases")
st.markdown("- **Phase 1:** Food Inventory\n- **Phase 2:** Morning Check-in and Daily Meal Plan")
st.caption("Morning Check-in records date, weight, sleep hours, soreness, and optional notes. Meal logging (what you actually ate), schedules/constraints, and analytics are not built yet.")
