# Voice Input and Meal Commands (Phases 1 and 3)

The **Voice Input** page lets you dictate a meal description, edit the transcription, and apply it to a selected date's saved meal plan. Speech recognition uses the browser Web Speech API. Routine command interpretation uses deterministic Python rules; it does not call any AI provider.

## Speech recognition and privacy

The app does not send audio to any AI or transcription API. This does not guarantee that recognition runs entirely on-device: browser vendors may process speech through their own services. Recognition support and quality vary by browser and device. Review browser speech-privacy settings before dictating sensitive details.

## Use it

1. Open **Voice Input & Meal Commands** in the Streamlit sidebar.
2. Select **Start speaking**, allow microphone access, and dictate in English.
3. Select **Stop speaking** when finished.
4. Correct the transcription in the review box.
5. Choose the date whose plan should be updated.
6. Select **Apply to meal plan** and review the confirmation or clarification message.

The saved plan for the selected date appears below the form. The **Daily Meal Plan** page remains available for direct manual editing.

## Supported deterministic commands

- **Initial plan:** label meals, e.g. `Breakfast: two bananas and milk. Lunch: three rotis and paneer bhurji. Dinner: dal rice.`
- **Replace a meal:** `Change my lunch to dal rice.`
- **Add to a meal:** `Add a banana to breakfast.`
- **Remove a meal:** `Remove dinner.`

Recognized meal slots are breakfast, morning snack, lunch, afternoon/evening snack, dinner, and other. The generic word `snack` is ambiguous and triggers a clarification. If a slot is missing, repeated in the same initial plan, or has multiple existing entries, the app asks the user to clarify rather than guessing.

For this phase, meal contents are stored as text in the existing `planned_meals` rows. Ingredient parsing, nutrition calculation, AI suggestions, and actual-consumption logging are not included.

## Troubleshooting

- If voice recognition is unavailable or returns no speech, type or paste into the review box.
- Allow microphone access for the app site. Remote deployments generally require HTTPS for microphone access.
- Chrome was manually confirmed to transcribe speech during development; Brave compatibility has not been resolved.
- If a command is not recognized, use a clear meal label or make the change on the Daily Meal Plan page.
