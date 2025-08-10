#!/bin/bash
# Exposes the local FastAPI server to the internet using ngrok.
# Requires ngrok to be installed and configured.

# Default port for the FastAPI app
PORT=${1:-8000}

echo "Starting ngrok tunnel for http://localhost:${PORT}"
ngrok http ${PORT}
