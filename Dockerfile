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
    rm -rf /var/lib/apt/lists/* 


RUN mkdir -p /opt/airflow/data/bronze \
             /opt/airflow/data/silver/btc_silver \
             /opt/airflow/data/silver/btc_features \
             /opt/airflow/logs && \
    chown -R airflow:root /opt/airflow/data /opt/airflow/logs && \
    chmod -R 775 /opt/airflow/data /opt/airflow/logs

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH
# Important : PYTHONPATH pour que Airflow trouve src/
ENV PYTHONPATH=/opt/airflow

USER airflow

COPY requirements.txt /requirements.txt
 # Attention : ne pas utiliser --no-deps pour pyspark
 RUN pip install --no-cache-dir -r /requirements.txt

 # 4️⃣ Installer PySpark avec toutes ses dépendances (y compris py4j)
 RUN pip install --no-cache-dir pyspark