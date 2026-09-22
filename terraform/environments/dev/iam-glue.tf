resource "aws_iam_role" "cms_proj_glue_role"{
  
  name = "cms_proj_glue_role"

  assume_role_policy = jsonencode({
    
    Version = "2012-10-17",
    
    Statement = [
      {
        "Effect": "Allow",
        
        "Principal": {
          "Service":"glue.amazonaws.com"
        },

        "Action": "sts:AssumeRole"        
      }
    ]
  })

  tags= {
    DEALabs = "MedicareProject"
  }
}


resource "aws_iam_policy" "cms_proj_glue_policy" {
  
  name = "cms_proj_glue_policy"

  policy= jsonencode({
    
    Version: "2012-10-17",
    
    Statement: [
      {
        Sid = "S3ListBucketPermissions",
        
        Effect = "Allow",
        
        Action = [
          "s3:ListBucket"
        ],

        Resource = [
          "arn:aws:s3:::medicare-cms-data-cjk-2026",
          aws_s3_bucket.cms_proj_python_scripts.arn
        ]
      },      
      {
        Sid = "S3ReadWritePermissions",
        
        Effect = "Allow",
        
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
        ],
        
        Resource = [
          "arn:aws:s3:::medicare-cms-data-cjk-2026/prod/01-raw/*",
          "arn:aws:s3:::medicare-cms-data-cjk-2026/dev/01-raw/*",
          "arn:aws:s3:::medicare-cms-data-cjk-2026/prod/02-silver/*",
          "arn:aws:s3:::medicare-cms-data-cjk-2026/dev/02-silver/*",
          "arn:aws:s3:::medicare-cms-data-cjk-2026/prod/03-gold/*",
          "arn:aws:s3:::medicare-cms-data-cjk-2026/dev/03-gold/*",
          "${aws_s3_bucket.cms_proj_python_scripts.arn}/*"
        ]
      },
      {
        Sid    = "GlueLogging",
        
        Effect = "Allow",
        
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        
        Resource = [
          "arn:aws:logs:us-east-1:440107864885:log-group:/aws-glue/jobs/output:*",
          "arn:aws:logs:us-east-1:440107864885:log-group:/aws-glue/jobs/error:*",
          "arn:aws:logs:us-east-1:440107864885:log-group:/aws-glue/jobs/logs-v2:*"
        ]
      },
      {
          "Sid": "AllowLogGroupCreationIfMissing",
          
          "Effect": "Allow",
          
          "Action": "logs:CreateLogGroup",
          
          "Resource": "arn:aws:logs:us-east-1:440107864885:log-group:/aws-glue/jobs/*"
      }            
    ]
  })

  tags= {
    DEALabs = "MedicareProject"
  }
}


resource "aws_iam_role_policy_attachment" "cms_proj_glue_policy_attachment"{
  role = aws_iam_role.cms_proj_glue_role.name
  policy_arn = aws_iam_policy.cms_proj_glue_policy.arn
} 
