# 🚀 Quant-AI : Infrastructure Distribuée de Prédiction BTC/USDT (T+10 min)

Projet de plateforme "end-to-end" pour la collecte, le traitement distribué (PySpark) et la prédiction haute fréquence du prix du Bitcoin.

## 👥 L'Équipe (Quant-AI)
* **Karima Chami** : Lead Data Engineer (Ingestion, Pipeline Medallion, PySpark,Feature Engineering)
* **El Bahia Boudal** : Lead Machine Learning Engineer ( Modélisation, Evaluation, Airflow)
* **Hamza Aslikh** : Lead Backend & Security Engineer (FastAPI, JWT, Docker, API Documentation)

---

## 🏗️ Architecture du Système

Le projet repose sur une architecture de données de type **Medallion** pour garantir la qualité et la traçabilité des prédictions :

1.  **Zone Bronze** : Ingestion des données brutes (OHLCV) depuis l'API Binance via des scripts Python.
2.  **Zone Silver** : Nettoyage, typage et enrichissement (Feature Engineering) via **PySpark** pour le calcul distribué.
3.  **Service Layer** : Modèle de régression entraîné pour prédire le prix à $T+10$ minutes et exposition via une API sécurisée.



---

## 🛠️ Stack Technique
* **Langage** : Python 3.12
* **Big Data** : PySpark (Traitement distribué)
* **Orchestration** : Apache Airflow
* **Machine Learning** : Scikit-learn / Spark ML
* **Base de données** : PostgreSQL
* **Backend** : FastAPI + JWT (JSON Web Tokens) + SQLAlchemy
* **Conteneurisation** : Docker & Docker Compose

---

## 📈 Pipeline de Données & IA

### 1. Ingestion (Data Engineering)
Collecte des K-lines (bougies) 1 minute sur Binance. Stockage initial en zone Bronze.

### 2. Feature Engineering (PySpark)
Calcul distribué des indicateurs techniques :
* **Variations (Returns)** : $Return = \frac{Close_{t-1}}{Close_t} - 1$
* **Moyennes Mobiles** : MA(5) et MA(10) via des fenêtres glissantes (`Window`).
* **Taker Ratio** : Analyse de l'agressivité des acheteurs/vendeurs.
* **Target (Label)** : Création de la cible $y = Close_{t+10}$ via la fonction `lead()`.

### 3. Modélisation (ML)
Entraînement d'un modèle de régression pour minimiser le **RMSE** et le **MAE**. Le modèle est sérialisé pour être servi en temps réel par l'API.

* **Algorithme** : Régression sur séries temporelles.
* **Évaluation** : Suivi des métriques RMSE et MAE pour garantir la fiabilité des prédictions.
---

## 🔒 Backend & Sécurité (FastAPI)

L'API REST sécurisée permet de consommer les prédictions en temps réel.

### 🔑 Sécurité & Auth
* **JWT (JSON Web Tokens)** : Authentification obligatoire pour accéder aux endpoints de prédiction.
* **Hachage** : Mots de passe sécurisés en base de données via `bcrypt`.

### 📡 Endpoints
| Méthode | Route | Description | Accès |
| :--- | :--- | :--- | :--- |
| `POST` | `/signup` | Création d'un compte utilisateur. | Public |
| `POST` | `/token` | Obtention du Token Access JWT. | Public |
| `POST` | `/predict/manual` | Inférence ML en temps réel (via `MLEngine`). | **Privé (JWT)** |

---
---

## 🚀 Installation et Lancement

### Pré-requis
* Docker & Docker Compose
* Compte API Binance (optionnel pour le mode démo)

### Déploiement
1. **Cloner le dépôt** :
   ```bash
   git clone (https://github.com/OclaZ/brief_12_Quant_AI)
   cd brief_12_Quant_AI
    ```

2. **Lancer les services Docker** :
   ```bash
   docker-compose up --build
   ```
3. **Accéder à l'API** :
    Ouvrir `http://localhost:8000/docs` pour la documentation interactive.
4. **Accéder à Airflow** :
    Ouvrir `http://localhost:8080` pour le tableau de bord Airflow.
5. **Accéder à PostgreSQL** :
    Utiliser un client PostgreSQL pour se connecter à `localhost:5432`.

### 📁 Structure du Projet 

📁 brief_12_Quant_AI/
├── airflow/
│   ├── dags/
│   │   └── dag_test.py
│   └── logs/
├── api/
│   ├── app/
│       ├── auth.py
│       ├── config.py
│       ├── database.py
│       ├── main.py
│       ├── ml_engine.py
│       ├── models.py
│       ├── routes.py
│       └── schemas.py
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── requirements.txt
├── data/
│   ├── bronze/
│       └── bronze.parquet
│   └── postgres/
│       └── save_to_postgres.py
│   ├── silver/
│       ├── btc_features/
│       └── btc_silver/
├── ml/
│   ├── models/
│   └── eda.ipynb
├── src/
│   ├── ingestion/
│       └── binance_ingestion.py
│   ├── processing/
│       ├── bronze_to_silver.ipynb
│       ├── bronze_to_silver.py
│       ├── silver_to_features.ipynb
│       └── silver_to_features.py
├── docker-compose.yml
├── Dockerfile
├── README.md
└── requirements.txt


## ⚙️ Orchestration des Flux (Apache Airflow)

L'automatisation est gérée par un DAG optimisé utilisant le décorateur `@dag` et des opérateurs spécialisés pour Spark. Le pipeline s'exécute **toutes les 10 minutes** pour transformer la donnée brute en prédiction actionnable.


### 🔄 Workflow du Pipeline
Le DAG `btc_bronze_silver_features_pipeline` orchestre la montée en qualité de la donnée :

1.  **Ingestion Bronze (`@task`)** :
    * Script : `src/ingestion/binance_ingestion.py` (Responsable : **Karima**)
    * Action : Récupère les données OHLCV via l'API Binance et initialise la zone **Bronze**.

2.  **Transformation Silver (`SparkSubmitOperator`)** :
    * Script : `src/processing/bronze_to_silver.py`
    * Action : Nettoyage des types, gestion des valeurs manquantes et formatage Spark.

3.  **Feature Engineering (`SparkSubmitOperator`)** :
    * Script : `src/processing/silver_to_features.py` (Responsable : **El Bahia**)
    * Action : Calcul des indicateurs techniques (Returns, MA5, MA10, Taker Ratio) et de la cible $T+10$.

4.  **Export Production (`SparkSubmitOperator`)** :
    * Script : `src/processing/save_to_postgres.py` (Responsable : **Hamza**)
    * Action : Chargement des features enrichies dans la base **PostgreSQL** (via driver JDBC) pour l'API REST.
5.  **Entraînement ML (`@task`)** :
    * Script : `ml/train_model.py`
    * Action : Entraînement périodique du modèle de régression et sérialisation pour l'inférence.

### 🛠️ Détails Techniques du DAG
* **ID du DAG** : `btc_bronze_silver_features_pipeline`
* **Fréquence** : `*/10 * * * *` (Toutes les 10 minutes).
* **Spark Master** : `local[*]` pour le parallélisme sur tous les cœurs disponibles.
* **Gestion des erreurs** : 2 tentatives (`retries`) avec un délai de 2 minutes pour pallier les micro-coupures réseau.
* **Dépendances JAR** : Utilisation du driver `postgresql-42.6.0.jar` pour la persistance des données.
