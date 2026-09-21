resource "aws_iam_role" "cms_proj_lambda_role"{
  
  name = "cms_proj_lambda_role"

  assume_role_policy = jsonencode({
    
    Version = "2012-10-17",
    
    Statement = [
      {
        "Effect": "Allow",
        
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },

        "Action": "sts:AssumeRole"        
      }
    ]
  })

  tags= {
    DEALabs = "MedicareProject"
  }

}



resource "aws_iam_policy" "cms_proj_lambda_policy" {
  
  name = "cms_proj_lambda_policy"

  policy= jsonencode({
    
    Version: "2012-10-17",
    
    Statement: [
      
      {
        Sid = "SecretsManagerSessionPermission",
        
        Effect = "Allow",
        
        Action = [
          "secretsmanager:GetSecretValue",
        ],
        
        Resource = data.aws_secretsmanager_secret.gdrive_file_secret.arn
      },
      {
        Sid = "S3ReadWritePermissions",
        
        Effect = "Allow",
        
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ],
        
        Resource = [
          "arn:aws:s3:::medicare-cms-data-cjk-2026/prod/01-raw/*",
          "arn:aws:s3:::medicare-cms-data-cjk-2026/dev/01-raw/*"
        ]
      },
      {
        Sid    = "LambdaLogging",
        
        Effect = "Allow",
        
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        
        Resource = "arn:aws:logs:us-east-1:440107864885:log-group:/aws/lambda/move_gdrive_files_to_s3:*"
      }            
    ]
  })

  tags= {
    DEALabs = "MedicareProject"
  }
}



resource "aws_iam_role_policy_attachment" "cms_proj_lambda_policy_attachment"{
  role = aws_iam_role.cms_proj_lambda_role.name
  policy_arn = aws_iam_policy.cms_proj_lambda_policy.arn
} 
