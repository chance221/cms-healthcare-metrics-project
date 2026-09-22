#!/bin/bash
set -euo pipefail

dnf update -y 
dnf install -y python3.13 python3.13-pip unzip

AIRFLOW_HOME=/opt/airflow
mkdir -p "$AIRFLOW_HOME"

AIRFLOW_VERSION=3.3.2
PYTHON_VERSION=3.13
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-$${AIRFLOW_VERSION}/constraints-$${PYTHON_VERSION}.txt"

python3.13 -m pip install "apache-airflow[amazon]==$${AIRFLOW_VERSION}" --constraint "$CONSTRAINT_URL"

# Pull the DAG/pyspark_jobs/configs bundle 
aws s3 cp "s3://${code_bucket}/${code_key}" /opt/airflow-bundle.zip
unzip -o /opt/airflow-bundle.zip -d "$AIRFLOW_HOME"

# A plain backgrounded process would die the moment the box reboots or the
# process crashes -- a systemd unit makes Airflow start on every boot and
# restart itself automatically if it ever goes down.
cat > /etc/systemd/system/airflow.service <<'UNIT'
[Unit]
Description=Apache Airflow standalone
After=network.target

[Service]
Environment=AIRFLOW_HOME=/opt/airflow
Environment=AWS_DEFAULT_REGION=us-east-1
ExecStart=/usr/bin/python3.13 -m airflow standalone
Restart=on-failure
User=root

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now airflow.service