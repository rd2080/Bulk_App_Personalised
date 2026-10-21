"""Voice input and deterministic application of reviewed meal commands."""

import streamlit as st
from datetime import date

from bulking_app.meal_commands import apply_meal_commands
from bulking_app.repositories.meal_plan import list_meals
from bulking_app.voice_input import browser_speech_input

st.set_page_config(page_title="Voice Input | Bulk App", page_icon="🎙️", layout="centered")
st.title("Voice Input & Meal Commands")
st.caption("Speak your plan, review the transcription, then apply it to a selected date.")
st.info(
    "Transcription uses your browser's built-in speech recognition. Routine meal "
    "commands are processed with Python rules and do not call Gemini or OpenAI. "
    "Browser vendors may handle speech recognition remotely."
)

if "voice_transcription" not in st.session_state:
    st.session_state.voice_transcription = ""

try:
    result = browser_speech_input(key="meal_voice_input")
    if isinstance(result, dict):
        if result.get("status") == "success" and result.get("transcript"):
            st.session_state.voice_transcription = result["transcript"]
        elif result.get("status") in {"unsupported", "error", "empty"}:
            st.warning(
                "Voice recognition is unavailable or returned no speech. Type or paste "
                "your meal description below instead."
            )
except Exception:
    st.warning("The voice control could not start. Enter or paste your meal description below.")

with st.form("voice_review_form"):
    reviewed_text = st.text_area(
        "Review and edit your transcription",
        key="voice_transcription",
        height=180,
        placeholder="Breakfast: two bananas and milk. Lunch: three rotis and paneer bhurji. Dinner: dal rice.",
        help="Correct any speech-recognition errors before applying the text.",
    )
    plan_date = st.date_input("Apply to plan date", value=date.today(), key="voice_plan_date")
    submitted = st.form_submit_button("Apply to meal plan", type="primary")

if submitted:
    if not reviewed_text.strip():
        st.warning("Enter or dictate a meal description before continuing.")
    else:
        try:
            outcome = apply_meal_commands(reviewed_text, plan_date)
            st.session_state.reviewed_voice_input = reviewed_text.strip()
            if outcome["status"] == "success":
                st.success(outcome["message"])
                for change in outcome["changes"]:
                    st.write(f"- {change}")
            else:
                st.warning(outcome["message"])
        except (RuntimeError, ValueError) as exc:
            st.error(str(exc))

st.divider()
selected_date = st.session_state.get("voice_plan_date", date.today())
st.subheader(f"Saved plan for {selected_date.isoformat()}")
try:
    saved_meals = list_meals(selected_date)
    if not saved_meals:
        st.info("No meals saved for this date yet. Describe your plan above to get started.")
    else:
        for meal in saved_meals:
            st.markdown(f"**{meal['meal_type']} — {meal['meal_name']}**")
            if meal["description"]:
                st.caption(meal["description"])
except RuntimeError as exc:
    st.error(str(exc))

st.caption(
    "Supported commands include a daily plan with meal labels (Breakfast, Lunch, Dinner, "
    "Morning snack, Evening snack), and explicit add/replace/remove instructions. "
    "If a command is ambiguous, the app asks for clarification instead of guessing. "
    "Use the Daily Meal Plan page for direct manual editing."
)
