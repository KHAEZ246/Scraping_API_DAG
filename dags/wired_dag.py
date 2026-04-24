from airflow import DAG
# Import PythonOperator yang baru sesuai warning di log Airflow kamu
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import requests

# CONFIG
API_URL = "http://api:8000/articles"

DB_CONFIG = {
    "host": "postgres",
    "database": "airflow",
    "user": "airflow",
    "password": "airflow"
}

# TASK 1: FETCH DATA
def fetch_data(ti):
    response = requests.get(API_URL)
    data = response.json()

    # Ekstrak list artikel yang sebenarnya dari dalam struktur JSON
    if isinstance(data, list) and len(data) > 0:
        # Jika struktur JSON sama persis dengan output scraper [ { session_id... } ]
        actual_articles = data[0].get("articles", [])
    elif isinstance(data, dict):
        # Jika API mengembalikan dictionary langsung { session_id... }
        actual_articles = data.get("articles", [])
    else:
        actual_articles = data

    # Push hanya list artikelnya saja
    ti.xcom_push(key="articles", value=actual_articles)


# TASK 2: TRANSFORM DATA
def transform_data(ti):
    articles = ti.xcom_pull(key="articles", task_ids="fetch_data")

    cleaned = []
    for art in articles:
        author = art.get("author", "")


        cleaned.append({
            "title": art.get("title"),
            "url": art.get("url"),
            "description": art.get("description"),
            "author": author,
            # Perbaikan Typo: disesuaikan dengan key dari scraper (scrapped_at)
            "scraped_at": art.get("scrapped_at") 
        })

    ti.xcom_push(key="cleaned_articles", value=cleaned)


# TASK 3: LOAD TO POSTGRES
def load_to_db(ti):
    articles = ti.xcom_pull(key="cleaned_articles", task_ids="transform_data")

    pg_hook = PostgresHook(postgres_conn_id="postgres_default")

    pg_hook.run("""
        CREATE TABLE IF NOT EXISTS wired_articles (
            id SERIAL PRIMARY KEY,
            title TEXT,
            url TEXT,
            description TEXT,
            author TEXT,
            scraped_at TIMESTAMP
        );
    """)

    for art in articles:
        pg_hook.run("""
            INSERT INTO wired_articles (title, url, description, author, scraped_at)
            VALUES (%s, %s, %s, %s, %s)
        """, parameters=(
            art["title"],
            art["url"],
            art["description"],
            art["author"],
            art["scraped_at"]
        ))

default_args = {
    'owner' : 'airflow',
    'depends_on_past' : False,
    'retries' : 1,
    'retry_delay' : timedelta(minutes=1),
}

with DAG(
    dag_id="wired_pipeline",
    default_args = default_args,
    description = 'DAG ambil data wired.com',
    start_date=datetime(2026, 4, 20),
    schedule = '*/5 * * * *',
    catchup=False
) as dag:

    task_fetch = PythonOperator(
        task_id="fetch_data",
        python_callable=fetch_data
    )

    task_transform = PythonOperator(
        task_id="transform_data",
        python_callable=transform_data
    )

    task_load = PythonOperator(
        task_id="load_to_db",
        python_callable=load_to_db
    )

    # urutan task
    task_fetch >> task_transform >> task_load