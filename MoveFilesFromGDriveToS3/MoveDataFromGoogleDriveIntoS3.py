"""
Lands CSV files from a Google Drive folder into the S3 raw layer.

Runs two ways, both calling the same stream_drive_to_s3() core -- they only
differ in where credentials come from and how parameters are supplied:

  - lambda_handler(event, context): the AWS Lambda entry point. 

  - main(): a local CLI entry point for testing before this is deployed.
"""

import argparse
import io
import json
import os
import re

import boto3
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive"]



def validate_period(value: str) -> str:
    if not re.match(r"^\d{4}Q[1-4]$", value):
        raise ValueError(f"period must be in YYYYQ# format (e.g. 2026Q3), got '{value}'")
    return value


def stream_drive_to_s3(
    drive_service,
    s3_client,
    s3_bucket: str,
    env: str,
    period: str,
    gdrive_folder_id: str,
    file_name_contains: str | None = None,
) -> list[str]:
    validate_period(period)

    query = f"'{gdrive_folder_id}' in parents and name contains '.gz' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if file_name_contains:
        files = [f for f in files if file_name_contains in f["name"]]

    if not files:
        print(f"No matching .gz files found in Drive folder {gdrive_folder_id}.")
        return []

    uploaded_keys = []
    for file in files:
        file_id = file["id"]
        file_name = file["name"]

        # Create an in-memory byte buffer
        file_stream = io.BytesIO()

        print(f"Streaming {file_name} from Google Drive into memory...")
        request = drive_service.files().get_media(fileId=file_id)
        downloader = MediaIoBaseDownload(file_stream, request)

        done = False
        while not done:
            _status, done = downloader.next_chunk()

        # Reset stream pointer to the beginning before uploading
        file_stream.seek(0)

        # Result: dev/01-raw/2026Q3/filename.csv 
        s3_key = f"{env}/01-raw/{period}/{file_name}"

        print(f"Uploading to s3://{s3_bucket}/{s3_key}...")
        s3_client.upload_fileobj(file_stream, s3_bucket, s3_key)
        file_stream.close()

        uploaded_keys.append(s3_key)
        print(f"Successfully processed {file_name}")

    return uploaded_keys


def lambda_handler(event, context):
    """
    Event payload (per-invocation, varies by call):
      {
        "period": "2021Q4",                             # required
        "gdrive_folder_id": "1AbC...",                   # required
        "env": "dev",                                     # required, defaults to "dev"
        "file_name_contains": "PBJ_Daily_Nurse_Staffing" # optional
      }

    Lambda environment variables (set once per deployment via
    Terraform apply):
      S3_BUCKET_NAME, GCP_SERVICE_ACCOUNT_SECRET_NAME
    """
    period = event["period"]
    gdrive_folder_id = event["gdrive_folder_id"]
    file_name_contains = event.get("file_name_contains")
    env = event.get("env", "dev")

    print("SSL_CERT_FILE:", os.environ.get("SSL_CERT_FILE"))
    print("REQUESTS_CA_BUNDLE:", os.environ.get("REQUESTS_CA_BUNDLE"))

    s3_bucket = os.environ["S3_BUCKET_NAME"]
    
    secret_name = os.environ["GCP_SERVICE_ACCOUNT_SECRET_NAME"]

    secrets_client = boto3.client("secretsmanager")
    secret_value = secrets_client.get_secret_value(SecretId=secret_name)
    service_account_info = json.loads(secret_value["SecretString"])
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info, scopes=SCOPES
    )

    drive_service = build("drive", "v3", credentials=credentials)
    s3_client = boto3.client("s3")

    uploaded_keys = stream_drive_to_s3(
        drive_service, s3_client, s3_bucket, env, period, gdrive_folder_id, file_name_contains
    )
    return {"uploaded_keys": uploaded_keys}


def main() -> None:
    # Local CLI entry point for testing before this is deployed to Lambda.
    
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=".env.local")

    parser = argparse.ArgumentParser(
        description="Land Google Drive CSVs into S3 raw, partitioned by reporting period"
    )
    parser.add_argument("--env", required=True, choices=["local", "dev", "prod"])
    parser.add_argument("--period", required=True, help="Reporting period in YYYYQ# format, e.g. 2026Q3")
    parser.add_argument("--gdrive-folder-id", required=True)
    parser.add_argument(
        "--file-name-contains", default=None, help="Only transfer files whose name contains this substring"
    )
    args = parser.parse_args()

    validate_period(args.period)

    service_account_file = os.environ["GCP_SERVICE_ACCOUNT_FILE"]
    s3_bucket = os.environ["S3_BUCKET_NAME"]

    credentials = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=SCOPES
    )
    drive_service = build("drive", "v3", credentials=credentials)
    s3_client = boto3.client("s3")

    stream_drive_to_s3(
        drive_service, s3_client, s3_bucket, args.env, args.period, args.gdrive_folder_id, args.file_name_contains
    )


if __name__ == "__main__":
    main()
