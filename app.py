"""Bulk App entry point."""

import streamlit as st

st.set_page_config(page_title="Bulk App", page_icon="🏋️", layout="wide")

st.title("Bulk App")
st.write("Personal bulking assistant.")
st.info("Use the sidebar to open Food Inventory. Additional workflows will be added phase by phase.")

st.subheader("Current phase")
st.markdown("- **Phase 1:** Food Inventory")
st.caption("The inventory is the source of truth for foods available to future meal planning.")
