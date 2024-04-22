FROM bitnami/spark:3.5.0


WORKDIR /opt/bitnami/spark

RUN pip install py4j

COPY ./src/spark_pgsql/spark_processing.py ./spark_processing.py
COPY ./src/constants.py ./src/constants.py

ENV POSTGRES_DOCKER_USER=host.docker.internal
ARG POSTGRES_PASSWORD
ENV POSTGRES_PASSWORD=$POSTGRES_PASSWORD

