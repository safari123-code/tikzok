# ---------------------------
# Tikzok — Dockerfile
# ---------------------------

FROM python:3.11-slim

# ---------------------------
# Workdir
# ---------------------------
WORKDIR /app

# ---------------------------
# Install dependencies
# ---------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------
# Copy project
# ---------------------------
COPY . .

# ---------------------------
# Environment
# ---------------------------
ENV PYTHONUNBUFFERED=1

# Cloud Run fournit automatiquement PORT
ENV PORT=8080

# ---------------------------
# Start server
# ---------------------------
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app