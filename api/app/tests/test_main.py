from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

# On génère un user unique pour ne pas avoir d'erreur "User already exists" à chaque test
unique_user = f"tester_{uuid.uuid4().hex[:6]}"
unique_pass = "secret123"

def test_read_root():
    """Vérifie que l'API répond (Health check)"""
    # Note: Assure-toi d'avoir une route "/" dans main.py, sinon change pour "/docs"
    response = client.get("/docs")
    assert response.status_code == 200

def test_create_user():
    """Teste la création d'un compte"""
    response = client.post(
        "/api/v1/signup",
        json={"username": unique_user, "password": unique_pass},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == unique_user
    assert "id" in data

def test_login_and_token():
    """Teste le login et la récupération du Token JWT"""
    # 1. On se logue (Format Form-Data pour OAuth2)
    response = client.post(
        "/api/v1/token",
        data={"username": unique_user, "password": unique_pass},
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # 2. On teste une route protégée (ex: Prediction) sans le token -> Doit échouer (401)
    bad_resp = client.post("/api/v1/predict/manual", json={})
    assert bad_resp.status_code == 401

def test_prediction_endpoint():
    
    # 1. On récupère le token (l'utilisateur est déjà créé par test_create_user qui s'exécute avant)
    # Note : Pytest exécute souvent par ordre alphabétique, mais ici on ré-authentifie pour être sûr
    login_resp = client.post(
        "/api/v1/token",
        data={"username": unique_user, "password": unique_pass},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    
    # 2. On prépare les données (conforme au nouveau modèle Linear Regression)
    payload = {
        "timestamp": "2026-01-23T15:00:00",
        "return_1m": 0.005,
        "ma_5": 50000.0,
        "ma_10": 49500.0,
        "volume": 1200.0,
        "close_prev": 49800.0,
        "number_of_trades": 150,
        "taker_ratio": 0.7
    }

    # 3. On envoie la requête AVEC le header Authorization
    response = client.post(
        "/api/v1/predict/manual",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    # 4. Vérifications
    if response.status_code == 503:
        # Si le modèle n'est pas chargé (ex: erreur checksum), on veut le savoir via le test
        assert False, f"Le modèle ML n'est pas chargé (503): {response.json()}"
    
    assert response.status_code == 200
    data = response.json()
    
    # On vérifie qu'on a bien reçu une prédiction chiffrée
    assert "predicted_price" in data
    assert isinstance(data["predicted_price"], float)
    print(f"✅ Prédiction reçue : {data['predicted_price']}")