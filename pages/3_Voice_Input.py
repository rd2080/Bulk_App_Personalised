"""Voice-to-text input foundation for future meal-planning workflows."""

import streamlit as st

from bulking_app.voice_input import browser_speech_input

st.set_page_config(page_title="Voice Input | Bulk App", page_icon="🎙️", layout="centered")
st.title("Voice Input")
st.caption("Speak a meal description, review the words, then use the corrected text.")
st.info(
    "Transcription uses your browser's built-in speech recognition. The app does not "
    "send audio to Gemini, OpenAI, or a transcription API. Browser vendors may handle "
    "recognition remotely; see the privacy note below."
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
    st.warning(
        "The voice control could not start. Enter or paste your meal description below."
    )

with st.form("voice_review_form"):
    reviewed_text = st.text_area(
        "Review and edit your transcription",
        key="voice_transcription",
        height=180,
        placeholder="For example: Lunch is three rotis and paneer bhurji.",
        help="You can type here whether or not voice recognition is supported.",
    )
    submitted = st.form_submit_button("Use this text", type="primary")

if submitted:
    if reviewed_text.strip():
        st.session_state.reviewed_voice_input = reviewed_text.strip()
        st.success("Your reviewed text is ready to use.")
        st.text(st.session_state.reviewed_voice_input)
    else:
        st.warning("Enter or dictate some text before continuing.")

st.caption(
    "This Phase 1 page captures and reviews text; meal-plan processing is a later phase. "
    "Browser speech recognition support, accuracy, and audio privacy vary by browser. "
    "Review your browser's speech privacy settings before dictating sensitive details."
)
