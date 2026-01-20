import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


load_dotenv()

# Récupération des variables
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "password")
server = os.getenv("POSTGRES_SERVER", "db")
port = os.getenv("POSTGRES_PORT", "5432")
db_name = os.getenv("POSTGRES_DB", "quant_ai_db")

# Construction de l'URL de connexion
DATABASE_URL = f"postgresql://{user}:{password}@{server}:{port}/{db_name}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    try:
        # On tente une connexion simple
        with engine.connect() as connection:
            print(f"✅ Connexion réussie à : {DATABASE_URL}")
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")