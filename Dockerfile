# Use a lightweight official Python image as base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Prevent Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Send Python output straight to the terminal (no buffering)
ENV PYTHONUNBUFFERED=1

# Install uv to manage dependencies
RUN pip install uv

# Copy dependency definitions first to leverage layer caching
COPY pyproject.toml uv.lock .

# Install dependencies (creates .venv automatically)
RUN uv sync --frozen --no-dev

# Add the virtual environment to PATH so its binaries are used by default
ENV PATH="/app/.venv/bin:$PATH"

# Copy the rest of the application code
COPY . .

# Port Flask listens on (default 5000)
EXPOSE 5000

# Start the application, listening on all container interfaces
CMD ["uv", "run", "flask", "--app", "wsgi", "run", "--host=0.0.0.0"]