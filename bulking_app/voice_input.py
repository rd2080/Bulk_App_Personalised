"""Native browser speech recognition Streamlit component."""

from pathlib import Path

import streamlit.components.v1 as components

_component = components.declare_component(
    "bulk_app_browser_speech",
    path=str(Path(__file__).parent / "components" / "browser_speech"),
)


def browser_speech_input(language: str = "en-US", key: str = "browser_speech") -> dict:
    """Return a browser transcription or an availability/error status."""
    return _component(language=language, key=key, default={"status": "ready"})
