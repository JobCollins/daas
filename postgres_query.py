"""
this script accesses the postgresql database
return a geodataframe table of disasters, conflict datasets
"""
import os
import yaml
import geopandas as gpd
from sqlalchemy import create_engine

config_path = os.getenv('CONFIG_PATH', 'config.yaml')
# print(config_path)
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

db_engine_url = config['db_engine_url']

engine = create_engine(db_engine_url)

def read_data_db(table_name):
    query = f"SELECT * FROM {table_name}"
    gdf = gpd.GeoDataFrame.from_postgis(query, engine, geom_col="geometry")
    return gdf