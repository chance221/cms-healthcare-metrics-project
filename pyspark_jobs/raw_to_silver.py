import argparse
import re

from pyspark.sql import functions as F
from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from pyspark.sql.window import Window

from pyspark_jobs.common.config_loader import load_all_dataset_configs, load_all_environment_configs
from pyspark_jobs.common.config_models import DatasetConfig, EnvironmentConfig
from pyspark_jobs.common.io_utils import safe_write, overwrite_partitions, read_current, resolve_path
from pyspark_jobs.common.spark_session import build_spark_session

SPARK_TYPE_MAP = {
    "string": StringType(),
    "int": IntegerType(),
    "long": LongType(),
    "double": DoubleType(),
    "timestamp": TimestampType(),
    "boolean": BooleanType(),
}


def to_spark_schema(columns) -> StructType:
    return StructType([
        StructField(c.name, SPARK_TYPE_MAP[c.type], nullable=c.nullable)
        for c in columns
    ])


def validate_period(value: str) -> str:
    if not re.match(r"^\d{4}Q[1-4]$", value):
        raise argparse.ArgumentTypeError(
            f"period must be in YYYYQ# format (e.g. 2026Q3), got '{value}'"
        )
    return value

#This is the check to ensure that if the raw headers name and position in our dtaset config doesn't
# match what's in the config the jobs fials early and loudly
def verify_raw_header(spark, raw_path: str, dataset_config: DatasetConfig) -> None:

    # Extra columns are only ever tolerated at the END of the header, and
    # only by exact name via ignore_extra_columns. 
    expected_headers = [c.expected_raw_header for c in dataset_config.schema_]
    actual_headers = spark.read.option("header", True).csv(raw_path).columns

    comparable_headers = actual_headers
    if len(actual_headers) > len(expected_headers):
        trailing = actual_headers[len(expected_headers):]
        if all(col in dataset_config.ignore_extra_columns for col in trailing):
            comparable_headers = actual_headers[:len(expected_headers)]

    if comparable_headers != expected_headers:
        raise ValueError(
            f"Raw header drift detected for '{dataset_config.dataset_name}'.\n"
            f"Expected ({len(expected_headers)}): {expected_headers}\n"
            f"Actual   ({len(actual_headers)}): {actual_headers}\n"
            f"ignore_extra_columns: {dataset_config.ignore_extra_columns}"
        )


def derive_measurement_period(df, source_column: str):

    # The source_column is a raw MM/DD/YYYY string parse it, then reduce to a standardized YYYYQ#
    parsed_date = F.to_date(F.col(source_column), "MM/dd/yyyy")
    return df.withColumn(
        "measurement_period",
        F.concat(F.year(parsed_date), F.lit("Q"), F.quarter(parsed_date))
    )


def run_dataset(spark,
                dataset_config: DatasetConfig,
                env_config: EnvironmentConfig,
                period: str) -> None:
    spark_schema = to_spark_schema(dataset_config.schema_)


    raw_glob = dataset_config.raw.prefix_pattern.format(env=env_config.env, period=period)
    raw_path = resolve_path(env_config, raw_glob)

    verify_raw_header(spark, raw_path, dataset_config)

    df_raw = (
        spark.read
        .schema(spark_schema)
        .option("header", True)
        .csv(raw_path)
    )

    if df_raw.isEmpty():
        print(f"WARNING: [{dataset_config.dataset_name}] raw file at {raw_path} matched 0 data rows.")

    if dataset_config.dedup_order_by is not None:
        window = (
            Window.partitionBy(*dataset_config.primary_key)
            .orderBy(F.col(dataset_config.dedup_order_by).desc())
        )
        df_raw = (
            df_raw
            .withColumn("_rn", F.row_number().over(window))
            .filter(F.col("_rn") == 1)
            .drop("_rn")
        )

    silver_relative_path = dataset_config.silver.output_path.format(env=env_config.env)
    silver_path = resolve_path(env_config, silver_relative_path)

    df_raw_tagged = (
        df_raw
        .withColumn("_silver_loaded_at", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

    if dataset_config.partition_source_column is not None:
        
        df_final = derive_measurement_period(df_raw_tagged, dataset_config.partition_source_column)
        overwrite_partitions(spark, df_final, silver_path, partition_column="measurement_period")
    else:
        df_silver = read_current(spark, env_config, silver_path)
        if df_silver is None:
            df_silver = spark.createDataFrame([], spark_schema)

        if "_silver_loaded_at" not in df_silver.columns:
            df_silver = (
                df_silver
                .withColumn("_silver_loaded_at", F.lit(None).cast("timestamp"))
                .withColumn("_source_file", F.lit(None).cast("string"))
            )

        if dataset_config.delete_missing_keys:
            df_final = df_raw_tagged
        else:
            df_kept = df_silver.join(df_raw_tagged, on=dataset_config.primary_key, how="left_anti")
            df_final = df_kept.unionByName(df_raw_tagged, allowMissingColumns=True)

        
        final_row_count = df_final.count()
        safe_write(spark, df_final, silver_path, run_id=period, strategy=env_config.write_strategy)
        print(f"[{dataset_config.dataset_name}] silver row count: {final_row_count}")
        return

    print(f"[{dataset_config.dataset_name}] silver row count: {df_final.count()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the generic SCD1 raw-to-silver job")
    parser.add_argument("--env", required=True, choices=["local", "dev", "prod"])
    parser.add_argument("--period", required=True, type=validate_period, help="Reporting period in YYYYQ# format (e.g. 2026Q3), substituted into the raw path template")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dataset", help="dataset_name of a single dataset config to run")
    group.add_argument("--all", action="store_true", help="run every dataset config")
    args, _unknown_args = parser.parse_known_args()

    env_configs, env_errors = load_all_environment_configs()
    if env_errors:
        raise RuntimeError(f"Cannot start: environment configs are invalid: {env_errors}")
    env_matches = [c for c in env_configs.values() if c.env == args.env]
    if not env_matches:
        raise ValueError(f"No environment config found with env='{args.env}'")
    env_config = env_matches[0]

    dataset_configs, dataset_errors = load_all_dataset_configs()
    if dataset_errors:
        raise RuntimeError(f"Cannot start: dataset configs are invalid: {dataset_errors}")

    if args.all:
        datasets_to_run = list(dataset_configs.values())
    else:
        datasets_to_run = [c for c in dataset_configs.values() if c.dataset_name == args.dataset]
        if not datasets_to_run:
            raise ValueError(f"No dataset config found with dataset_name='{args.dataset}'")

    spark = build_spark_session(env_config, app_name="raw-to-silver")
    try:
        for dataset_config in datasets_to_run:
            run_dataset(spark, dataset_config, env_config, args.period)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
