data "archive_file" "move_from_gdrive_to_s3_zip"{
  
  type = "zip"
  
  output_path = "${path.module}/MoveDataFromGoogleDriveIntoS3.zip"

  source_file = "${path.module}/../../../MoveFilesFromGDriveToS3/MoveDataFromGoogleDriveIntoS3.py"
}



data "archive_file" "google_deps_zip"{
  
  type = "zip"
  
  output_path = "${path.module}/google-layer.zip"

  source_dir = "${path.module}/../../../MoveFilesFromGDriveToS3/lambda_layer"

  excludes = [
    "python/urllib3",
    "python/urllib3-2.8.0.dist-info",
    "python/certifi",
    "python/certifi-2026.7.22.dist-info"
  ]
}



resource "aws_lambda_layer_version" "google_deps_layer"{
  
  filename = data.archive_file.google_deps_zip.output_path
  
  layer_name = "google-api-dependencies"
  
  compatible_runtimes = ["python3.13"]

  source_code_hash = data.archive_file.google_deps_zip.output_base64sha256
  
  description = "Pre zipped google-api-python-client and google-auth dependencies"
}



resource "aws_lambda_function" "move_gdrive_files_to_s3"{
  
  filename = data.archive_file.move_from_gdrive_to_s3_zip.output_path
  
  function_name = "move_gdrive_files_to_s3"
  
  role = aws_iam_role.cms_proj_lambda_role.arn
  
  handler = "MoveDataFromGoogleDriveIntoS3.lambda_handler"
  
  runtime = "python3.13"
  
  source_code_hash = data.archive_file.move_from_gdrive_to_s3_zip.output_base64sha256
  
  layers = [aws_lambda_layer_version.google_deps_layer.arn]

  timeout = 900

  memory_size = 1024

  environment {
    
    variables = {
      S3_BUCKET_NAME = aws_s3_bucket.medicare_s3_data_lake.id
      GCP_SERVICE_ACCOUNT_SECRET_NAME = data.aws_secretsmanager_secret.gdrive_file_secret.name
    }
  }
}