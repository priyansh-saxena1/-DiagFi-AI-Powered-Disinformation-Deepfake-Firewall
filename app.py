# This file is the entry point for the Hugging Face Spaces environment.
# It simply imports the FastAPI app object from the main application module.
from app.main import app

# The application is run via the Dockerfile's CMD instruction,
# which calls `uvicorn app.main:app`.
# If you were to run this file directly, you would use:
# uvicorn app:app --host 0.0.0.0 --port 7860
#
# The `app` object needs to be available in this file for the
# Hugging Face platform to detect and run it.
