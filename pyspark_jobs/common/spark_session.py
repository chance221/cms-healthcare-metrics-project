import os
import sys

import boto3
from pyspark.sql import SparkSession
from botocore.exceptions import ProfileNotFound

from pyspark_jobs.common.config_models import EnvironmentConfig


# Ivy resolves hadoop-aws's transitive deps (software.amazon.awssdk:bundle)
# automatically — don't hand-pin the SDK bundle version separately.
S3_JAR_PACKAGES = "org.apache.hadoop:hadoop-aws:3.5.0"


def build_spark_session(env_config: EnvironmentConfig, 
                        app_name: str) -> SparkSession:
    
    # Windows: without this, executor subprocesses try to launch "python3",
    # which doesn't exist on a standard Windows Python install.
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    builder = (
        SparkSession.builder
        .appName(app_name)

        # Without this, a partitioned overwrite wipes the ENTIRE target path before writing
        # Instead dynamic mode replaces only the partitions present in the new DataFrame
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
    )

    # spark_master is None for prod — Glue provisions its own Spark context
    # and manages its own executor/driver memory.
    if env_config.spark_master is not None:
        builder = builder.master(env_config.spark_master).config("spark.driver.memory", "6g")

    if env_config.write_strategy == "aws":
        try:
            creds = boto3.Session(profile_name=env_config.aws_profile).get_credentials().get_frozen_credentials()
        except ProfileNotFound:
            creds = boto3.Session().get_credentials().get_frozen_credentials()

        if creds.token:
            provider = "org.apache.hadoop.fs.s3a.TemporaryAWSCredentialsProvider"
        else :
            provider = "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider"


        builder = (
            builder
            .config("spark.jars.packages", S3_JAR_PACKAGES)
            .config("spark.hadoop.fs.s3a.aws.credentials.provider", provider)
            .config("spark.hadoop.fs.s3a.access.key", creds.access_key)
            .config("spark.hadoop.fs.s3a.secret.key", creds.secret_key)
        )

        if creds.token:
            builder = builder.config("spark.hadoop.fs.s3a.session.token", creds.token)

    return builder.getOrCreate()
