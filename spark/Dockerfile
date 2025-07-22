FROM bitnami/spark:3.5.0
USER root
RUN pip install pyspark==3.5.0 delta-spark==3.1.0
COPY transform.py /app/transform.py
WORKDIR /app
USER 1001
