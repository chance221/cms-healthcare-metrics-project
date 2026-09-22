resource "aws_iam_role" "ec2_airflow_role"{
  name = "ec2_airflow_role"

  assume_role_policy = jsonencode({
    
    Version = "2012-10-17"
    
    Statement = [{

      Action = "sts:AssumeRole"
      
      Effect = "Allow"

      Principal = { Service = "ec2.amazonaws.com"}
    }]
  })
}



resource "aws_iam_policy" "ec2_airflow_run_policy" {

  name = "ec2_airflow_run_policy"

  policy = jsonencode({
    
    Version = "2012-10-17"

    Statement = [
      {
        Sid = "AllowLambdaInvoke"

        Effect = "Allow"

        Action = [
          "lambda:InvokeFunction"
        ]

        Resource = [
          aws_lambda_function.move_gdrive_files_to_s3.arn
        ]
      },
      {
        Sid = "AllowGlueJobManagement"

        Effect = "Allow"

        Action = [
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:GetJobRuns",
          "glue:GetJob"
        ]

        Resource = [
          aws_glue_job.cms_proj_silver_to_gold_glue_job.arn,
          aws_glue_job.cms_proj_raw_to_silver_glue_job.arn
        ]
      },     
      {
        Sid = "AllowS3GetObject"

        Effect = "Allow"

        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]

        Resource = [
          "${aws_s3_bucket.cms_proj_python_scripts.arn}/*",
          "${aws_s3_bucket.medicare_s3_data_lake.arn}/*"
        ]
      },
      {
        Sid    = "S3BucketReadPermissions"
        
        Effect = "Allow"
        
        Action = [
          "s3:GetAccelerateConfiguration", "s3:GetBucketAcl", "s3:GetBucketCORS",
          "s3:GetBucketLogging", "s3:GetBucketObjectLockConfiguration", "s3:GetBucketPolicy",
          "s3:GetBucketPublicAccessBlock", "s3:GetBucketRequestPayment", "s3:GetBucketTagging",
          "s3:GetBucketVersioning", "s3:GetBucketWebsite", "s3:GetEncryptionConfiguration",
          "s3:GetLifecycleConfiguration", "s3:GetReplicationConfiguration", "s3:ListBucket"
        ]
        
        Resource = [
          "arn:aws:s3:::medicare-cms-data-cjk-2026",
          "arn:aws:s3:::cms-project-python-scripts-cjk-2026"
        ]
      }
    ]
  })
}




resource "aws_iam_role_policy_attachment" "ec2_airflow_sms_policy_attach" {
  
  role       = aws_iam_role.ec2_airflow_role.name
  
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}





resource "aws_iam_role_policy_attachment" "ec2_airflow_run_policy_attach" {
  
  role       = aws_iam_role.ec2_airflow_role.name
  
  policy_arn = aws_iam_policy.ec2_airflow_run_policy.arn
}


resource "aws_iam_instance_profile" "ec2_airflow_profile" {
  
  name = "airflow-ec2-instance-profile"
  
  role = aws_iam_role.ec2_airflow_role.name
}