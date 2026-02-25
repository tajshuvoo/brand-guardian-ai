# -----------------------------
# Base Image
# -----------------------------
FROM python:3.12-slim

# -----------------------------
# System Config
# -----------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# -----------------------------
# Install uv
# -----------------------------
RUN pip install --no-cache-dir uv

# -----------------------------
# Copy dependency files first
# (better Docker layer caching)
# -----------------------------
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# -----------------------------
# Copy full project
# -----------------------------
COPY . .

# -----------------------------
# Expose FastAPI port
# -----------------------------
EXPOSE 8000

# -----------------------------
# Start FastAPI
# -----------------------------
CMD ["uv", "run", "uvicorn", "backend.src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]