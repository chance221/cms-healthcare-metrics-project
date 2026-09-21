data "archive_file" "pyspark_jobs_zip" {
  
  type = "zip"
  
  output_path = "${path.module}/pyspark_jobs.zip"

  dynamic "source" {
    
    for_each = fileset("${path.module}/../../../pyspark_jobs", "**/*.py")
    
    content {
      
      filename = "pyspark_jobs/${source.value}"
      
      content  = file("${path.module}/../../../pyspark_jobs/${source.value}")
    }
  }
}

data "archive_file" "config_files_zip" {
  
  type = "zip"
  
  output_path = "${path.module}/config_files.zip"

  dynamic "source" {
    
    for_each = fileset("${path.module}/../../../configs", "**/*.{yml,yaml}")
    
    content {
      
      filename = "configs/${source.value}"
      
      content  = file("${path.module}/../../../configs/${source.value}")
    }
  }
}


resource "aws_s3_object" "pyspark_jobs_upload" {
  
  bucket = aws_s3_bucket.cms_proj_python_scripts.id
  
  key = "pyspark_jobs.zip"
  
  source = data.archive_file.pyspark_jobs_zip.output_path
  
  etag = data.archive_file.pyspark_jobs_zip.output_md5
}



resource "aws_s3_object" "configs_upload" {
  
  bucket = aws_s3_bucket.cms_proj_python_scripts.id
  
  key = "configs.zip"
  
  source = data.archive_file.config_files_zip.output_path
  
  etag = data.archive_file.config_files_zip.output_md5
}



resource "aws_s3_object" "raw_to_silver_upload" {

  bucket = aws_s3_bucket.cms_proj_python_scripts.id

  key = "raw_to_silver.py"

  source = "${path.module}/../../../pyspark_jobs/raw_to_silver.py"

  etag = filemd5("${path.module}/../../../pyspark_jobs/raw_to_silver.py")
}



resource "aws_s3_object" "silver_to_gold_upload" {

  bucket = aws_s3_bucket.cms_proj_python_scripts.id

  key = "silver_to_gold.py"

  source = "${path.module}/../../../pyspark_jobs/silver_to_gold.py"

  etag = filemd5("${path.module}/../../../pyspark_jobs/silver_to_gold.py")
}



resource "aws_glue_job" "cms_proj_raw_to_silver_glue_job"{

  name = "cms_proj_raw_to_silver_glue_job"

  role_arn = aws_iam_role.cms_proj_glue_role.arn

  glue_version = "6.0"

  command {
    
    name = "glueetl"
    
    script_location = "s3://${aws_s3_object.raw_to_silver_upload.bucket}/${aws_s3_object.raw_to_silver_upload.key}"
  }

  default_arguments = {
    
    "--extra-py-files" = "s3://${aws_s3_object.pyspark_jobs_upload.bucket}/${aws_s3_object.pyspark_jobs_upload.key}"

    "--extra-files" = "s3://${aws_s3_object.configs_upload.bucket}/${aws_s3_object.configs_upload.key}"
    
    "--PIPELINE_CONFIG_ROOT" = "."

    "--additional-python-modules" = "pydantic==2.13.4,pyyaml==6.0.3" 
  }
}



resource "aws_glue_job" "cms_proj_silver_to_gold_glue_job"{

  name = "cms_proj_silver_to_gold_glue_job"

  role_arn = aws_iam_role.cms_proj_glue_role.arn

  glue_version = "6.0"

  command {
    
    name = "glueetl"
    
    script_location = "s3://${aws_s3_object.silver_to_gold_upload.bucket}/${aws_s3_object.silver_to_gold_upload.key}"
  }

  default_arguments = {
    
    "--extra-py-files" = "s3://${aws_s3_object.pyspark_jobs_upload.bucket}/${aws_s3_object.pyspark_jobs_upload.key}"

    "--extra-files" = "s3://${aws_s3_object.configs_upload.bucket}/${aws_s3_object.configs_upload.key}"
    
    "--PIPELINE_CONFIG_ROOT" = "."

    "--additional-python-modules" = "pydantic==2.13.4,pyyaml==6.0.3" 
  }
}


