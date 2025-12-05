from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

from datetime import datetime, timedelta
import os, json, requests, pandas as pd
from sqlalchemy import create_engine, text

from urllib.parse import quote_plus

DATA_DIR = "/tmp"
os.makedirs(DATA_DIR, exist_ok=True)

RAW_PATH = f"{DATA_DIR}/weather_raw.json"
CLEAN_PATH = f"{DATA_DIR}/weather_clean.csv"

CITY = "Rio de Janeiro"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


def _pg_url_from_env(database: str = "postgres") -> str:
    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    port = os.getenv("DB_PORT", "5432")
    
    # URL-encode password to handle special characters
    encoded_password = quote_plus(password)

    print(f"Connecting to Supabase: {host}:{port}/{database} with user {user}")
    return f"postgresql+psycopg2://{user}:{encoded_password}@{host}:{port}/{database}?sslmode=require"

def _ensure_schema_exists(engine):
    try:
        with engine.begin() as conn:
            conn.execute(text("SET search_path TO public"))
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS weather"))
            
        print("Schema 'weather' ensured to exist")
    except Exception as e:
        print(f"Schema creation failed: {e}")
        raise

def _ensure_table_exists(engine):

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS weather.weather_data (
        id SERIAL PRIMARY KEY,
        city VARCHAR(100) NOT NULL,
        temperature_K FLOAT NOT NULL,
        humidity FLOAT NOT NULL,
        thermal_sensation_K FLOAT NOT NULL,
        temp_min_K FLOAT NOT NULL,
        temp_max_K FLOAT NOT NULL,
        pressure FLOAT,
        wind_speed FLOAT,
        wind_direction FLOAT,
        latitude FLOAT NOT NULL,
        longitude FLOAT NOT NULL,
        temperature_C FLOAT NOT NULL,
        thermal_sensation_C FLOAT NOT NULL,
        temp_min_C FLOAT NOT NULL,
        temp_max_C FLOAT NOT NULL,
        weather_id INT NOT NULL,
        weather_main VARCHAR(100) NOT NULL,
        weather_description VARCHAR(255) NOT NULL,
        weather_icon VARCHAR(100) NOT NULL,
        sys_id INT NOT NULL,
        sys_country VARCHAR(100) NOT NULL,
        sys_sunrise TIMESTAMP NOT NULL,
        sys_sunset TIMESTAMP NOT NULL,
        collection_timestamp TIMESTAMP NOT NULL
    )
    """
    
    try:
        with engine.begin() as conn:
            conn.execute(text(create_table_sql))
            
        print("Table 'weather.weather_data' ensured to exist with correct schema and NOT NULL constraints")
    except Exception as e:
        print(f"Table creation failed: {e}")
        raise


def extract():
    if not OPENWEATHER_API_KEY:
        raise ValueError("OPENWEATHER_API_KEY is not set")
    
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={OPENWEATHER_API_KEY}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()
    with open(RAW_PATH, "w") as f:
        json.dump(data, f)

    return data

def transform():
    
    with open(RAW_PATH, "r") as f:
        data = json.load(f)

    df = pd.json_normalize(data)

    #Normalize weather data
    weather_data = df['weather'][0][0]
    
    df['weather_id'] = weather_data['id']
    df['weather_main'] = weather_data['main']
    df['weather_description'] = weather_data['description']
    df['weather_icon'] = f"https://openweathermap.org/img/wn/{weather_data['icon']}@2x.png"

    df['sys_sunrise'] = df['sys.sunrise'] + df['timezone']
    df['sys_sunset'] = df['sys.sunset'] + df['timezone']
    
    df['sys_sunrise'] = pd.to_datetime(df['sys_sunrise'], unit='s').dt.round('ms')
    df['sys_sunset'] = pd.to_datetime(df['sys_sunset'], unit='s').dt.round('ms')

    # Add timestamp
    df['collection_timestamp'] = pd.Timestamp.now()

    columns_to_keep = {
        'name': 'city',
        'main.temp': 'temperature_k',
        'main.humidity': 'humidity',
        'main.feels_like': 'thermal_sensation_k',
        'main.temp_min': 'temp_min_k',
        'main.temp_max': 'temp_max_k',
        'main.pressure': 'pressure',
        'wind.speed': 'wind_speed',
        'wind.deg': 'wind_direction',
        'coord.lat': 'latitude',
        'coord.lon': 'longitude',
        'weather_id': 'weather_id',
        'weather_main': 'weather_main',
        'weather_description': 'weather_description',
        'weather_icon': 'weather_icon',
        'sys.id': 'sys_id',
        'sys.country': 'sys_country',
        'sys_sunrise': 'sys_sunrise', 
        'sys_sunset': 'sys_sunset', 
        'collection_timestamp': 'collection_timestamp'
    }

    available_cols = {k: v for k, v in columns_to_keep.items() if k in df.columns}

    df_transformed = df[list(available_cols.keys())].copy()
    df_transformed.rename(columns=available_cols, inplace=True)

    k_cols = [col for col in df_transformed.columns if '_k' in col]

    for col in k_cols:
        col_c = col.replace('_k', '_c')

        df_transformed[col_c] = df_transformed[col] - 273.15

    df_transformed.to_csv(CLEAN_PATH, index=False)
    return df_transformed

def load():
    
    df = pd.read_csv(CLEAN_PATH)

    engine = create_engine(
        _pg_url_from_env(),
        pool_pre_ping=True,
        connect_args={"sslmode": "require", "connect_timeout": 10},        
    )

    _ensure_schema_exists(engine)
    _ensure_table_exists(engine)

    try: 
        with engine.connect() as conn:
            df.to_sql("weather_data", conn, if_exists="append", index=False, schema="weather")
    except Exception as e:
        print("Error loading data into database")
        raise
    finally:
        engine.dispose()

    return True


with DAG(
    dag_id="weather_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule_interval=timedelta(minutes=2),
    catchup=False,
    tags=["weather_pipeline"],
) as dag:

    t_extract = PythonOperator(
        task_id="extract",
        python_callable=extract,
    )

    t_transform = PythonOperator(
        task_id="transform",
        python_callable=transform,
    )

    t_load = PythonOperator(
        task_id="load",
        python_callable=load,
    )

    t_extract >> t_transform >> t_load