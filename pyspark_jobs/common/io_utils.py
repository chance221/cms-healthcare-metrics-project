import shutil
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession

from pyspark_jobs.common.config_models import DatasetConfig, EnvironmentConfig, GoldConfig

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_DATA_ROOT = REPO_ROOT / "data"


def resolve_path(env_config: EnvironmentConfig,
                 relative_path: str) -> str:
    if env_config.write_strategy == "aws":
        return f"s3a://{env_config.s3_bucket}/{relative_path}"
    return str(LOCAL_DATA_ROOT / relative_path)


def resolve_pandas_path(env_config: EnvironmentConfig,
                        relative_path: str) -> str:
    # Spark's Hadoop S3 connector expects s3a://; pandas reads S3 through
    # s3fs, which expects plain s3://. 
    return resolve_path(env_config, relative_path).replace("s3a://", "s3://", 1)


def read_current(spark: SparkSession, 
                 env_config: EnvironmentConfig, 
                 target_path: str) -> DataFrame | None:
    if env_config.write_strategy == "aws":
        pointer_path = f"{target_path}/_LATEST"
        try:
            run_id = spark.read.text(pointer_path).collect()[0][0]
        except Exception:
            return None
        return spark.read.parquet(f"{target_path}/run={run_id}")
    else:
        try:
            return spark.read.parquet(target_path)
        except Exception:
            return None


def read_silver_dataset(spark: SparkSession, env_config: EnvironmentConfig, dataset_config: DatasetConfig) -> DataFrame:
    
    # read_current's local/rename vs aws/manifest resolution (Phase 1).
    silver_relative_path = dataset_config.silver.output_path.format(env=env_config.env)
    silver_path = resolve_path(env_config, silver_relative_path)

    if dataset_config.partition_source_column is not None:
        return spark.read.parquet(silver_path)

    df = read_current(spark, env_config, silver_path)
    if df is None:
        raise RuntimeError(
            f"No silver data found for dataset '{dataset_config.dataset_name}' at {silver_path} — "
            f"run raw_to_silver.py for this dataset first."
        )
    return df


def read_gold_dataset(spark: SparkSession, env_config: EnvironmentConfig, gold_config: GoldConfig) -> DataFrame:
    # Gold outputs are always a plain overwrite parquet write .
    output_relative_path = gold_config.output_path.format(env=env_config.env)
    output_path = resolve_path(env_config, output_relative_path)
    try:
        return spark.read.parquet(output_path)
    except Exception:
        raise RuntimeError(
            f"No gold data found for dataset '{gold_config.gold_dataset_name}' at {output_path} — "
            f"run silver_to_gold.py for this dataset first."
        )


def overwrite_partitions(spark: SparkSession, df: DataFrame, target_path: str, partition_column: str) -> None:
    (
        df.repartition(partition_column)
        .write
        .mode("overwrite")
        .partitionBy(partition_column)
        .parquet(target_path)
    )


def safe_write(spark: SparkSession,
                 df: DataFrame,
                 target_path: str,
                 run_id: str,
                 strategy: str,
                 partition_column: str | None = None) -> None:
    if strategy == "aws":
        #Create a run path that will hold the data.
        run_path = f"{target_path}/run={run_id}"
        writer = df.write.mode("overwrite")
        if partition_column is not None:
            writer = writer.partitionBy(partition_column)
        writer.parquet(run_path)
        (
            spark.createDataFrame([(run_id,)], ["run_id"])
            .coalesce(1)
            .write.mode("overwrite")
            .text(f"{target_path}/_LATEST")
        )
    elif strategy == "local":
        # Local disk rename is atomic — write to a temp dir, then swap.
        temp_path = f"{target_path}__tmp_{run_id}"
        writer = df.write.mode("overwrite")
        if partition_column is not None:
            writer = writer.partitionBy(partition_column)
        writer.parquet(temp_path)
        if Path(target_path).exists():
            shutil.rmtree(target_path)
        shutil.move(temp_path, target_path)
    else:
        raise ValueError(f"Unknown write strategy: {strategy}")
