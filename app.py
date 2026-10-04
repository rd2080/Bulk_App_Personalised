"""Bulk App entry point."""

import streamlit as st

st.set_page_config(page_title="Bulk App", page_icon="🏋️", layout="wide")

st.title("Bulk App")
st.write("Personal bulking assistant.")
st.info("Open Food Inventory or Morning Check-in from the sidebar.")

st.subheader("Current phases")
st.markdown("- **Phase 1:** Food Inventory\n- **Phase 2:** Morning Check-in")
st.caption("Morning Check-in records date, weight, sleep hours, soreness, and optional notes. Meal planning, meal logging, schedules/constraints, and analytics are not part of these phases.")
