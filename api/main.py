from http.client import HTTPException

# FastAPIというライブラリから、FastAPIクラスを読み込む
from fastapi import FastAPI
# PostgreSQL接続用ライブラリ
import psycopg
# データ検証ライブラリ
from pydantic import BaseModel
# DBデータを辞書型で取得する用
from psycopg.rows import dict_row
# ブラウザのオリジンを許可
from fastapi.middleware.cors import CORSMiddleware
# 環境変数設定ファイル読み込み用
import os
from dotenv import load_dotenv

import pandas as pd
import geopandas as gpd
import json

# FastAPIアプリケーションの本体を作成する
# この「app」が、API全体の入口になる
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQLへの接続情報
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


# HTTPのGETリクエストで「/」にアクセスされたときに実行する
# @app.get("/") は「/というURLへのGET処理を登録する」という意味
@app.get("/")
def read_root():
    # {"message": "Hello Onsen GIS"} という辞書を返す
    # FastAPIが自動的にJSON形式に変換してくれる
    return {"message": "Hello Onsen GIS"}


# @app.get("/") は「/というURLへのGET処理を登録する」という意味
@app.get("/hot-springs")
def get_hot_springs():

    # PostgreSQLへ接続する
    with psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        row_factory=dict_row
    ) as conn:

        # SQLを実行するためのカーソルを作成
        with conn.cursor() as cur:

            # 温泉データの件数を取得
            query_str = "SELECT id,name,latitude,longitude,address,quality,ph,temperature,geology,visited,description FROM public.hot_springs"
            cur.execute(query_str)

            # SQLの結果を全行取得
            rows = cur.fetchall()

            # GeoJsonに変換
            df = pd.DataFrame(rows)

            # decimalはJSONにできないため、floatに変換
            numeric_columns = [
                "latitude",
                "longitude",
                "ph",
                "temperature",
            ]

            for column in numeric_columns:
                if column in df.columns:
                    df[column] = df[column].astype(float)

            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(
                    df["longitude"],
                    df["latitude"]
                ),
                crs="EPSG:4326"
            )
            return json.loads(gdf.to_json())

@app.get("/hot-springs/{id}")
def get_hot_spring(
    id :int
):
    # PostgreSQLへ接続する
    with psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        row_factory=dict_row
    ) as conn:
        
        # SQLを実行するためのカーソルを作成
        with conn.cursor() as cur:

            # 温泉データの件数を取得
            query_str = """SELECT id,name,latitude,longitude,address,quality,ph,temperature,geology,visited,description FROM public.hot_springs
                           WHERE id = %s"""
            cur.execute(query_str,(id,))

            # SQLの結果を1行取得
            rows = cur.fetchone()

            # GeoJsonに変換
            df = pd.DataFrame([rows])

            # decimalはJSONにできないため、floatに変換
            numeric_columns = [
                "latitude",
                "longitude",
                "ph",
                "temperature",
            ]

            for column in numeric_columns:
                if column in df.columns:
                    df[column] = df[column].astype(float)

            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(
                    df["longitude"],
                    df["latitude"]
                ),
                crs="EPSG:4326"
            )
            return json.loads(gdf.to_json())


class VisitedUpdate(BaseModel):
    visited: bool

@app.put("/hot-springs/{id}/visited")
def update_visited(
    id: int,
    update_data: VisitedUpdate
):
        # PostgreSQLへ接続する
        with psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            row_factory=dict_row
        ) as conn:
            
            # SQLを実行するためのカーソルを作成
            with conn.cursor() as cur:
                query_str = """update public.hot_springs set visited = %s where id = %s returning id,visited"""
                cur.execute(query_str,(update_data.visited,id))
                result = cur.fetchone()

            if result is None:
                raise HTTPException(
                    status_code=404,
                    detail="温泉が見つかりません"
                )

            return {
                "id": result["id"],
                "visited": result["visited"]
            }