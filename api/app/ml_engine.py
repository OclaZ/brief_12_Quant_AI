import os
from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
from pyspark.ml.regression import LinearRegressionModel
from pyspark.ml.feature import VectorAssembler
from pyspark.sql.types import StructType, StructField, FloatType

class MLEngine:
    def __init__(self, model_path: str, feature_columns: list):
        self.model_path = model_path
        self.features_cols = feature_columns
        self.spark = None
        self.model = None
        self._initialize_spark()
        self._load_model()

    def _initialize_spark(self):
        print("⚡ [MLEngine] Initialisation de la session Spark...")
        self.spark = SparkSession.builder \
            .appName("QuantAI_API") \
            .master("local[*]") \
            .config("spark.driver.memory", "1g") \
            .config("spark.ui.enabled", "false") \
            .getOrCreate()

    def _load_model(self):
        if os.path.exists(self.model_path):
            print(f"[MLEngine] Chargement du modèle depuis : {self.model_path}")
            try:
                # Tentative 1 : Pipeline
                self.model = PipelineModel.load(self.model_path)
                print("✅ [MLEngine] Modèle chargé (Type: Pipeline).")
            except:
                try:
                    # Tentative 2 : Modèle simple
                    self.model = LinearRegressionModel.load(self.model_path)
                    print("✅ [MLEngine] Modèle chargé (Type: LinearRegression).")
                except Exception as e:
                    print(f"❌ [MLEngine] Erreur critique chargement : {e}")
                    self.model = None
        else:
            print(f"⚠️ [MLEngine] Aucun modèle trouvé à : {self.model_path}")

    def predict(self, data_dict: dict) -> float:
        if not self.model:
            raise RuntimeError("Le modèle ML n'est pas chargé.")

        # 1. Création DataFrame
        data_values = tuple(data_dict[col] for col in self.features_cols)
        schema = StructType([StructField(col, FloatType(), True) for col in self.features_cols])
        df = self.spark.createDataFrame([data_values], schema)

        # 2. Transformation & Prédiction
        predictions = None
        if isinstance(self.model, PipelineModel):
            predictions = self.model.transform(df)
        else:
            assembler = VectorAssembler(inputCols=self.features_cols, outputCol="features")
            df_assembled = assembler.transform(df)
            predictions = self.model.transform(df_assembled)

        # 3. Extraction résultat
        if 'prediction' in predictions.columns:
            return predictions.select("prediction").first()["prediction"]
        else:
            raise ValueError("Colonne 'prediction' manquante dans la sortie du modèle.")