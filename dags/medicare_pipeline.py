from airflow import DAG
from airflow.decorators import task
from airflow.models.param import Param
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from airflow.providers.amazon.aws.operators.lambda_function import LambdaInvokeFunctionOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
import json
RAW_TO_SILVER_GLUE_JOB = "cms_proj_raw_to_silver_glue_job"
SILVER_TO_GOLD_GLUE_JOB = "cms_proj_silver_to_gold_glue_job"
INGESTION_LAMBDA = "move_gdrive_files_to_s3"
DATA_BUCKET = "medicare-cms-data-cjk-2026"

PERIOD_PATTERN = r"^\d{4}Q[1-4]$"

with DAG(
    dag_id="medicare_pipeline",
    schedule=None,
    catchup=False,
    tags=["medicare", "pipeline"],
    params={
        "run_ingest": Param(True, type="boolean"),
        "run_raw_to_silver": Param(True, type="boolean"),
        "run_silver_to_gold": Param(True, type="boolean"),
        "env": Param("dev", enum=["local", "dev", "prod"]),
        "period": Param("2026Q3", type="string", pattern=PERIOD_PATTERN),
        "dataset": Param("all", type="string"),
        "gold_dataset": Param("all", type="string"),
        "gdrive_folder_id": Param("", type="string"),
        "file_name_contains": Param(None, type=["null", "string"]),
    },
) as dag:

    @task.short_circuit
    def should_ingest(**context):
        return context["params"]["run_ingest"]

    @task
    def build_ingestion_payload(**context):
        import os

        os.environ.pop('AWS_CA_BUNDLE', None)
        os.environ.pop('REQUESTS_CA_BUNDLE', None)

        p = context["params"]
        payload = {
            "period": p["period"],
            "gdrive_folder_id": p["gdrive_folder_id"],
            "env": p["env"],
        }
        if p["file_name_contains"]:
            payload["file_name_contains"] = p["file_name_contains"]

        return json.dumps(payload)
        

    check_ingest = should_ingest()
    payload_data = build_ingestion_payload()
    
    invoke_ingestion_lambda = LambdaInvokeFunctionOperator(
        task_id="invoke_ingestion_lambda",
        function_name=INGESTION_LAMBDA,
        payload=payload_data,
    )     


    @task.short_circuit(trigger_rule="none_failed_min_one_success")
    def should_raw_to_silver(**context):
        return context["params"]["run_raw_to_silver"]


    wait_for_raw_landing = S3KeySensor(
        task_id="wait_for_raw_landing",
        bucket_name=DATA_BUCKET,
        bucket_key="{{ params.env }}/01-raw/{{ params.period }}/",
        wildcard_match=True,
        timeout=60 * 30,
        poke_interval=30,
    )

    @task
    def build_raw_to_silver_args(**context):
        p = context["params"]
        args = {"--env": p["env"], "--period": p["period"]}
        if p["dataset"] == "all":
            args["--all"] = ""
        else:
            args["--dataset"] = p["dataset"]
        return args

    run_raw_to_silver_glue = GlueJobOperator(
        task_id="run_raw_to_silver_glue",
        job_name=RAW_TO_SILVER_GLUE_JOB,
        script_args=build_raw_to_silver_args(),
    )

    @task.short_circuit(trigger_rule="none_failed_min_one_success")
    def should_silver_to_gold(**context):
        return context["params"]["run_silver_to_gold"]

    @task
    def build_silver_to_gold_args(**context):
        p = context["params"]
        args = {"--env": p["env"]}
        if p["gold_dataset"] == "all":
            args["--all"] = ""
        else:
            args["--gold-dataset"] = p["gold_dataset"]
        return args

    run_silver_to_gold_glue = GlueJobOperator(
        task_id="run_silver_to_gold_glue",
        job_name=SILVER_TO_GOLD_GLUE_JOB,
        script_args=build_silver_to_gold_args(),
    )

    (
        check_ingest
        >> payload_data
        >> invoke_ingestion_lambda
        >> should_raw_to_silver()
        >> wait_for_raw_landing
        >> run_raw_to_silver_glue
        >> should_silver_to_gold()
        >> run_silver_to_gold_glue
    )
