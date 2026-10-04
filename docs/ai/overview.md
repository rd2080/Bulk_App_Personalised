# AI architecture

The application asks an AI provider to produce meal and workout plan content. Provider-specific code sits behind adapters and is called through the application service layer, keeping provider integration separate from the Streamlit interface and database.

Provider credentials are supplied through environment configuration locally and deployment secrets in Streamlit Cloud. Do not commit credentials. Generated plans are user-facing suggestions and should be reviewed before use.
