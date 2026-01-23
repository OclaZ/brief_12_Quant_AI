import requests
import pandas as pd
import os
SYMBOL = 'BTCUSDT'
INTERVAL = '1m'   # Intervalle d'une minute
LIMIT = 600        # Nombre de lignes à récupérer
BRONZE_PATH = "/opt/airflow/data/bronze/btc_bronze.parquet" 
def data_collection_api():
    response = requests.get(
        url='https://api.binance.com/api/v3/klines',
        params={
            "symbol": SYMBOL,
            "interval": INTERVAL,
            "limit": LIMIT
        }
    )
    
    if response.status_code != 200:
        print(f"Erreur {response.status_code}")
        return None
    
    data = response.json()
    
    columns = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
    ]
    df = pd.DataFrame(data, columns=columns)
    
    numeric_cols = ["open", "high", "low", "close", "volume",
                    "quote_asset_volume", "number_of_trades",
                    "taker_buy_base_volume", "taker_buy_quote_volume"]
    df[numeric_cols] = df[numeric_cols].astype(float)
    
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms").astype('datetime64[ms]')
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms").astype('datetime64[ms]')
    
    # --- AJOUT INDISPENSABLE ICI ---
    bronze_dir = os.path.dirname(BRONZE_PATH)
    os.makedirs(bronze_dir, exist_ok=True)
    
    # Sauvegarde effective des données pour que Spark puisse les lire
    df.to_parquet(BRONZE_PATH, index=False)
    # -------------------------------

    return f"Bronze data saved to {BRONZE_PATH}"