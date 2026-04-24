from fastapi import FastAPI
import json
import os

app = FastAPI()

DATA_PATH = "/data/articles.json"

@app.get("/articles")
def get_articles():
    if not os.path.exists(DATA_PATH):
        return {"message": "Data belum tersedia"}

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)