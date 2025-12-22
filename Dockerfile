# Utiliser une image Python officielle comme base
FROM python:3.11-slim

# Éviter les fichiers .pyc et activer le buffering des logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires pour Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    librandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Installer les navigateurs Playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# Copier le reste du code source
COPY . .

# Exposer le port (sera surchargé par Railway via $PORT)
EXPOSE 8000

# Commande de démarrage utilisant la variable d'environnement PORT
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
