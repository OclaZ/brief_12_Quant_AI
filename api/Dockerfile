# ON PASSE A PYTHON 3.9 (Version la plus stable pour la compatibilité)
FROM python:3.9-slim

WORKDIR /code

# 1. Installation de Java
RUN apt-get update && \
    apt-get install -y default-jdk procps && \
    apt-get clean;

ENV JAVA_HOME=/usr/lib/jvm/default-java

# 2. Installation des dépendances
COPY ./requirements.txt /code/requirements.txt
RUN pip install --default-timeout=1000 --no-cache-dir --upgrade -r /code/requirements.txt

# 3. Copie du code
COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]