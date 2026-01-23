# # FROM apache/airflow:2.8.1

# USER root

# # 1️⃣ Installer Java pour PySpark
# RUN apt-get update \
#     && apt-get install -y openjdk-17-jdk \
#     && apt-get clean

# ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
# ENV PATH=$JAVA_HOME/bin:$PATH

# # 2️⃣ Définir PYTHONPATH pour que Airflow voie src
# ENV PYTHONPATH=/opt/airflow:/opt/airflow/src

# USER airflow

# # 3️⃣ Copier requirements et installer les dépendances Python
# COPY requirements.txt /requirements.txt
# # Attention : ne pas utiliser --no-deps pour pyspark
# RUN pip install --no-cache-dir -r /requirements.txt

# # 4️⃣ Installer PySpark avec toutes ses dépendances (y compris py4j)
# RUN pip install --no-cache-dir pyspark

FROM apache/airflow:2.8.1

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /opt/airflow/data/silver/btc_features && \
    chmod -R 777 /opt/airflow/data

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Important : PYTHONPATH pour que Airflow trouve src/
ENV PYTHONPATH=/opt/airflow

USER airflow

RUN pip install --no-cache-dir \
    apache-airflow-providers-apache-spark \
    pyspark