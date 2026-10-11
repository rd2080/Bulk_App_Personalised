# Voice Input (Phase 1)

The **Voice Input** page lets you dictate a meal description, edit the resulting text, and submit the reviewed text for later use. It is a foundation for a later meal-planning phase; it does not interpret commands, modify a plan, or save meals.

## Speech recognition choice

The page uses the browser's native Web Speech recognition interface through a small Streamlit component included in the repository. The app does not transmit audio to a transcription service, nor does it call Gemini or OpenAI for transcription. It requires a supported browser and microphone permission. Recognition support and quality vary by browser and device.

“The app does not transmit audio” does not mean recognition is guaranteed to run entirely on-device. Browser vendors may process speech using their own services. Review the browser's speech and privacy settings before dictating sensitive information. The app does not separately upload or store microphone audio.

## Use it

1. Open **Voice Input** in the Streamlit sidebar.
2. Select **Start speaking**, allow microphone access, and dictate in English.
3. Select **Stop speaking** when finished.
4. Correct the transcription in the review box, or type/paste text there if voice recognition is unavailable.
5. Select **Use this text**. The page confirms the reviewed text; later phases can connect it to meal-plan processing.

## Troubleshooting

- If the microphone button is unavailable or recognition returns no text, use the text box directly.
- Allow microphone access for the app's site in browser settings. Remote deployments generally need HTTPS for microphone access.
- Try a current browser with Web Speech recognition support if the voice control is unavailable.
- Recognition errors, unsupported browsers, or denied permission do not prevent manual text entry.

The browser component uses no additional Python dependency. Its JavaScript relies on the browser Web Speech API; no audio-recognition library or cloud transcription SDK is added to the app.
