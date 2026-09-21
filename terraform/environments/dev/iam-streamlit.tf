resource "aws_iam_role" "ecs_streamlit_s3_role"{
  name = "ecs_streamlit_s3_role"

  assume_role_policy = jsonencode({
    
    Version = "2012-10-17"
    
    Statement = [{

      Action = "sts:AssumeRole"
      
      Effect = "Allow"

      Principal = { Service = "ecs-tasks.amazonaws.com"}
    }]
  })
}



resource "aws_iam_role" "ecs_streamlit_ecr_role"{
  name = "ecs_streamlit_ecr_role"

  assume_role_policy = jsonencode({
    
    Version = "2012-10-17"
    
    Statement = [{

      Action = "sts:AssumeRole"
      
      Effect = "Allow"

      Principal = { Service = "ecs-tasks.amazonaws.com"}
    }]
  })
}



resource "aws_iam_role" "ecs_express_infra_role" {
  
  name = "ecs_express_infra_role"

  assume_role_policy = jsonencode({
    
    Version = "2012-10-17"
    
    Statement = [{
      
      Action    = "sts:AssumeRole"
      
      Effect    = "Allow"
      
      Principal = { Service = "ecs.amazonaws.com" }
    }]
  })
}



resource "aws_iam_policy" "ecs_streamlit_ecr_access_policy"{
  
  name = "ecs_streamlit_ecr_access_policy"

  policy = jsonencode({

    Version: "2012-10-17"

    Statement: [
      {
        Sid    = "ECSEncryptedImagePull"
        
        Effect = "Allow"
        
        Action = [          
          "ecr:BatchGetImage",          
          "ecr:GetDownloadUrlForLayer"          
        ]
        
        Resource = aws_ecr_repository.cms_proj_streamlit.arn        
      },
      {
        Sid    = "ECSAgentAuthToken"
        
        Effect = "Allow"
        
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        
        Resource = "*"
      },
      {
        Sid    = "ECSCloudWatchLogging"
        
        Effect = "Allow"
        
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        
        Resource = "*" # Or point to your specific log group ARN
      }
    ]
  })
}




resource "aws_iam_policy" "ecs_streamlit_s3_policy" {
  
  name = "ecs_streamlit_s3_policy"

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
          "arn:aws:s3:::medicare-cms-data-cjk-2026"
        ]
      },      
      {
        Sid = "S3ReadWritePermissions"
        
        Effect = "Allow"
        
        Action = [
          "s3:GetObject"
        ],
        
        Resource = [
          "arn:aws:s3:::medicare-cms-data-cjk-2026/prod/03-gold/*",
          "arn:aws:s3:::medicare-cms-data-cjk-2026/dev/03-gold/*"
        ]
      }      
    ]
  })

  tags= {
    DEALabs = "MedicareProject"
  }
}



resource "aws_iam_role_policy_attachment" "ecs_streamlit_s3_policy_attachment"{
  
  role = aws_iam_role.ecs_streamlit_s3_role.name
  
  policy_arn = aws_iam_policy.ecs_streamlit_s3_policy.arn
}



resource "aws_iam_role_policy_attachment" "ecs_streamlit_ecr_access_policy_attachment"{
  
  role = aws_iam_role.ecs_streamlit_ecr_role.name
  
  policy_arn = aws_iam_policy.ecs_streamlit_ecr_access_policy.arn
}



resource "aws_iam_role_policy_attachment" "ecs_express_infra_attach" {
  
  role       = aws_iam_role.ecs_express_infra_role.name
  
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices"
}




