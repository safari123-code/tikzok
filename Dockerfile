# ---------------------------
# Tikzok — Dockerfile
# ---------------------------
FROM python:3.11-slim

WORKDIR /app

# Installer dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier application
COPY . .

# Variables Cloud Run
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Lancer serveur
CMD ["gunicorn","--bind","0.0.0.0:8080","--workers","2","--threads","4","--timeout","0","app:app"]