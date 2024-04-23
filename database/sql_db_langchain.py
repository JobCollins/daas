import os

from langchain.sql_database import SQLDatabase
from src.constants import POSTGRES_URL


url = POSTGRES_URL
TABLE_NAME = "rappel_conso_table"

db = SQLDatabase.from_uri(
    url,
    include_tables=[TABLE_NAME],
    sample_rows_in_table_info=1,
)
