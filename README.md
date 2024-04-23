# daas
LLM powered data engineering system with Kafka, Spark, Airflow, Postgres, and Docker.

The data pipeline:
1. Data Streaming - data streams from API into Kafka `topic`
2. Data Processing - Spark `job` processes the data and transfers it to a PostgreSQL database.
3. Scheduling - orchestrate the streaming and processing using Airflow.

## Setup

Install all packages
`pip install -r requirements.txt`

Create the airflow-kafka network
`docker network create airflow-kafka`

## Kafka Streaming

Start the kafka service
`docker-compose up`

visit the kafka-ui at http://localhost:8800/

On the left click on Topic and then Add a topic at the top left. Name it rappel-conso.

Since there is only one broker set the replication factor to 1. Also, set the partitions number to 1 since there will be only one consumer thread at a time so no need for parallelism. 

Finally, set the time to retain data to one hour since the spark job will run right after the kafka streaming task, so there is no need to retain the data for a long time in the kafka topic.


## PostgreSQL
Install postgres and pgAdmin4 https://www.postgresql.org/download/

Start pgAdmin4

Set your `POSTGRES_PASSWORD` in a `.env` file

Run the script to create a table in the DB with the command
`python scripts/create_table.py`



## Spark Setup: Consuming and Transfer of Data
Build the Docker image for Spark. Replace `$POSTGRES_PASSWORD` with your PostgreSQL password.

`docker build -f spark/Dockerfile -t rappel-conso/spark:latest --build-arg POSTGRES_PASSWORD=$POSTGRES_PASSWORD  .`


## Airflow Setup: Orchestration of Kafka and Spark
Create environment variables to be used by `docker-compose`.

`echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_PROJ_DIR=\"./airflow_resources\"" > .env`

`AIRFLOW_UID` represents the User ID in Airflow containers and `AIRFLOW_PROJ_DIR` represents the airflow project directory.

Run the airflow service.

`docker compose -f docker-compose-airfloe.yaml up`

Airflow runs on http://localhost:8080
Username and password is `airflow`

Search for the dag `kafka_spark_dag` and click on it.

Press the play button on your right to start the task. A task is successfully complete when it is green.

Go to pgAdmin4

Verify that the `rappel_conso_table` is filled with data
`SELECT count(*) FROM rappel_conso_table`


## Start the LLM Data Assistant Application

To start the LLM run
`streamlit run streamlit_app/app.py`