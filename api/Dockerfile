FROM python:3.11-slim

WORKDIR /code

# Installation des dépendances
COPY ./requirements.txt /code/requirements.txt

# AJOUT DE --default-timeout=1000 pour éviter l'erreur de connexion
RUN pip install --default-timeout=1000 --no-cache-dir --upgrade -r /code/requirements.txt

# Copie du code
COPY ./app /code/app

# Commande par défaut
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]