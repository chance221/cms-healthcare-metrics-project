import boto3
from pyspark.sql import SparkSession, Row
import os
import sys

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

PROFILE = "medicare-local-dev"
BUCKET = "medicare-analysis-project"
REGION = "us-east-1"   # match your bucket's actual region

# Resolve credentials via the profile you already set up
# Get the credentils from boto 3 then pass them to the spark session that needsaccess to the S3 bucket
creds = boto3.Session(profile_name=PROFILE).get_credentials().get_frozen_credentials()

spark = (
    SparkSession.builder
    .appName("local-s3-smoke-test")
    .master("local[*]")
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.5.0")
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
    .config("spark.hadoop.fs.s3a.access.key", creds.access_key)
    .config("spark.hadoop.fs.s3a.secret.key", creds.secret_key)
    .config("spark.hadoop.fs.s3a.endpoint.region", REGION)
    .getOrCreate()
)

df = spark.createDataFrame([Row(id=1, name="test"), Row(id=2, name="check")])

test_path = f"s3a://{BUCKET}/local/_smoke-test/df-test"
df.write.mode("overwrite").parquet(test_path)

df_read = spark.read.parquet(test_path)
df_read.show()

spark.stop()