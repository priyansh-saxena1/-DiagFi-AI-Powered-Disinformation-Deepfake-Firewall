# Stage 1: Build stage with uv
FROM python:3.11-slim as builder

# Install uv
RUN pip install uv

# Set up a non-root user
RUN useradd --create-home appuser
WORKDIR /home/appuser

# Copy requirements and install dependencies into a virtual environment
COPY requirements.txt .
RUN uv venv .venv && . .venv/bin/activate && uv pip install --no-cache-dir -r requirements.txt

# Stage 2: Final image
FROM python:3.11-slim as final

# Create a non-root user
RUN useradd --create-home appuser
USER appuser
WORKDIR /home/appuser

# Copy virtual environment from builder stage
COPY --from=builder /home/appuser/.venv ./.venv
ENV PATH="/home/appuser/.venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser app/ ./app

# Expose port and run the application
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
