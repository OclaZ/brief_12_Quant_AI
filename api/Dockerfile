# Base : Python 3.9 sur Debian Bullseye (Inclut Java 11 supporté par défaut)
FROM python:3.9-slim-bullseye

# Évite les fichiers .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV JAVA_HOME=/usr/lib/jvm/default-java

WORKDIR /code

# 1. Installation système & Java (Optimisée en une seule couche)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    default-jdk \
    procps \
    libpq-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Dépendances Python
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 3. Code Application
COPY ./app /code/app

# 4. Utilisateur non-root (Sécurité - Optionnel mais recommandé en prod)
# RUN useradd -m myuser
# USER myuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]