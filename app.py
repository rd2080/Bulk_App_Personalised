"""Streamlit morning check-in and daily plan review."""

import json
import os
from datetime import date

import streamlit as st
from dotenv import load_dotenv

from bulking_app.ai.factory import get_planner
from bulking_app.database import initialize_database
from bulking_app.services.tools import get_profile, recent_plans, save_daily_plan, save_profile

load_dotenv()
initialize_database()
st.set_page_config(page_title="Bulk App", page_icon="🏋️", layout="centered")
st.title("Your daily bulking check-in")
st.caption(f"{date.today().strftime('%A, %B %d, %Y')} · Local-first planning")

profile = get_profile()
with st.expander("Your profile", expanded=False):
    with st.form("profile_form"):
        name = st.text_input("Name (optional)", profile["name"])
        goal = st.text_input("Goal", profile["goal"])
        dietary_notes = st.text_area("Dietary notes or restrictions", profile["dietary_notes"])
        if st.form_submit_button("Save profile"):
            save_profile(name, goal, dietary_notes)
            st.success("Profile saved.")

st.subheader("Morning check-in")
weight = st.number_input("Today's weight (kg)", min_value=25.0, max_value=350.0,
                         value=70.0, step=0.1)
feeling = st.text_area("How are you feeling?", placeholder="Energy, appetite, soreness, sleep...")
food_text = st.text_area("Available foods", placeholder="One item per line. Add a quantity after a comma, e.g. oats, 80 g")
notes = st.text_area("Today's schedule or workout notes", placeholder="Time available, equipment, planned activity...")

foods = []
for line in food_text.splitlines():
    if line.strip():
        bits = line.split(",", 1)
        foods.append({"name": bits[0].strip(), "quantity": bits[1].strip() if len(bits) > 1 else ""})

provider = st.selectbox("AI provider", ["gemini", "openai"],
                        index=0 if os.getenv("AI_PROVIDER", "gemini").lower() == "gemini" else 1)
if st.button("Generate today's plan", type="primary"):
    try:
        context = {"date": str(date.today()), "profile": profile, "weight_kg": weight,
                   "feeling": feeling, "foods": foods, "notes": notes}
        st.session_state["draft_plan"] = get_planner(provider).generate_plan(context)
        st.session_state["draft_context"] = {"weight": weight, "feeling": feeling,
                                              "foods": foods, "notes": notes, "provider": provider}
    except Exception as exc:
        st.error(str(exc))

if "draft_plan" in st.session_state:
    st.subheader("Review your plan")
    st.write(st.session_state["draft_plan"])
    edited = st.text_area("Edit plan JSON before saving", json.dumps(
        st.session_state["draft_plan"], indent=2, ensure_ascii=False), height=320)
    if st.button("Save today's plan"):
        try:
            plan = json.loads(edited)
            draft = st.session_state["draft_context"]
            plan_id = save_daily_plan(weight_kg=draft["weight"], feeling=draft["feeling"],
                                      foods=draft["foods"], notes=draft["notes"], plan=plan,
                                      provider=draft["provider"])
            st.success(f"Plan saved (#{plan_id}).")
        except (ValueError, json.JSONDecodeError) as exc:
            st.error(f"Please check the plan and check-in fields: {exc}")

with st.expander("Recent saved plans"):
    for item in recent_plans():
        st.markdown(f"**{item['plan_date']} · {item['provider']}**")
        st.json(item["plan"])
