# daas
LLM powered data engineering system with Kafka, Spark, Airflow, Postgres, and Docker.

The data pipeline:
1. Data Streaming - data streams from API into Kafka `topic`
2. Data Processing - Spark `job` processes the data and transfers it to a PostgreSQL database.
3. Scheduling - orchestrate the streaming and processing using Airflow.
