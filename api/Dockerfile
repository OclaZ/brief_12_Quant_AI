FROM python:3.11-slim

WORKDIR /code

# 1. Installation de Java (OBLIGATOIRE pour PySpark)
RUN apt-get update && \
    apt-get install -y default-jdk procps && \
    apt-get clean;

ENV JAVA_HOME=/usr/lib/jvm/default-java

# 2. Installation des dépendances (C'est ici que pyspark s'installe)
COPY ./requirements.txt /code/requirements.txt
RUN pip install --default-timeout=1000 --no-cache-dir --upgrade -r /code/requirements.txt

# 3. Copie du code
COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]