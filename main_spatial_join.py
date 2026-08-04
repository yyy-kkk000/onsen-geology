import pandas as pd
import geopandas as gpd
import glob

# 温泉情報の読み込み(geojson)
gdf_onsen = gpd.read_file("aomori-onsen.geojson")

# シェープファイルから地質情報を取得
try:
    # フォルダ配下のすべてのシェープファイルパスを取得
    folder_path = "geologyData"
    shp_files = glob.glob(f"{folder_path}/**/*.shp", recursive=True)
except Exception as e:
    print(f"地質データの取得に失敗しました: {e}")
    exit()

# ファイルを読み込んでリストに格納
file_contents = []
for file in shp_files:
    file_contents.append(gpd.read_file(file))

gdf_geology = pd.concat(file_contents,ignore_index=True)
gdf_geology = gpd.GeoDataFrame(gdf_geology,geometry="geometry")

# CRSをそろえる
if gdf_onsen.crs != gdf_geology.crs:
    gdf_geology = gdf_geology.to_crs(gdf_onsen.crs)

# 空間結合
gdf_joined = gpd.sjoin(gdf_onsen,gdf_geology,how="left",predicate="within")

# 空間結合特有の不要な列（index_right）を削除（※任意・エラー防止）
# 既存のindex_right列があると、後続の処理や再結合でエラーの原因になります
if "index_right" in gdf_joined.columns:
    gdf_joined = gdf_joined.drop(columns=["index_right"])

# ファイル出力
gdf_joined.to_file("onsen_geology.geojson", driver="GeoJSON", encoding="utf-8")