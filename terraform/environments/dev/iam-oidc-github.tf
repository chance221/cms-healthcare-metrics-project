resource "aws_iam_role" "github_plan_role_dev"{
  
  name = "github_plan_role_dev"

  assume_role_policy = jsonencode({
    
    Version = "2012-10-17",
    
    Statement = [
      {
        "Effect": "Allow",
        
        "Principal": {
          "Federated": aws_iam_openid_connect_provider.github.arn
        },
        
        "Action": "sts:AssumeRoleWithWebIdentity",
        
        "Condition": {
            "StringEquals": {
                "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                "token.actions.githubusercontent.com:sub": "repo:chance221/cms-healthcare-metrics-project:pull_request"
            }
        }
      }
    ]
  })

  tags= {
    DEALabs = "MedicareProject"
  }

}



resource "aws_iam_role" "github_apply_role"{
  
  name = "github_apply_role"

  assume_role_policy = jsonencode({
    
    Version = "2012-10-17",
    
    Statement = [
      {
        "Effect": "Allow",
        
        "Principal": {
          "Federated": aws_iam_openid_connect_provider.github.arn
        },
        
        "Action": "sts:AssumeRoleWithWebIdentity",
        
        "Condition": {
            "StringEquals": {
                "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                "token.actions.githubusercontent.com:sub": "repo:chance221/cms-healthcare-metrics-project:environment:production"
            }
        }
      }
    ]
  })

  tags= {
    DEALabs = "MedicareProject"
  }

}



resource "aws_iam_role" "github_build_role"{
  
  name = "github_build_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        "Effect": "Allow",
        
        "Principal": {
          "Federated": aws_iam_openid_connect_provider.github.arn
        },
        
        "Action": "sts:AssumeRoleWithWebIdentity",
        
        "Condition": {
            "StringEquals": {
                "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                "token.actions.githubusercontent.com:sub": "repo:chance221/cms-healthcare-metrics-project/workflows/deploy.yml@refs/heads/main"
            }
        }
      }
    ]
  })

  tags= {
    DEALabs = "MedicareProject"
  }

}



resource "aws_iam_openid_connect_provider" "github"{
  
  url = "https://token.actions.githubusercontent.com"
  
  client_id_list = ["sts.amazonaws.com"]
  
  thumbprint_list = ["ab9d0263244dd0326eb67015705a667e79cfe998"]
  tags= {
    DEALabs = "MedicareProject"
  }
}



resource "aws_iam_policy" "github_dev_env_plan_policy" {
  
  name = "github_dev_env_plan_policy"

  policy= jsonencode({
    
    Version: "2012-10-17",
    
    Statement: [
      {
        Sid = "S3BucketManagementReadPermissions",
        Effect = "Allow",
        Action= [
          "s3:GetAccelerateConfiguration",
          "s3:GetBucketAcl",
          "s3:GetBucketCORS",
          "s3:GetBucketLogging",
          "s3:GetBucketObjectLockConfiguration",
          "s3:GetBucketPolicy",
          "s3:GetBucketPublicAccessBlock",
          "s3:GetBucketRequestPayment",
          "s3:GetBucketTagging",
          "s3:GetBucketVersioning",
          "s3:GetBucketWebsite",
          "s3:GetEncryptionConfiguration",
          "s3:GetLifecycleConfiguration",
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ],

        Resource = "arn:aws:s3:::medicare-pipeline-tf-state-cjk-2026"
      },
      {
        Sid = "S3GetObjectManagementReadPermissions",
        
        Effect = "Allow",
        
        Action = [
          "s3:GetObject"
        ],

        Resource = "arn:aws:s3:::medicare-pipeline-tf-state-cjk-2026/*"
      }      
    ]
  })

  tags= {
    DEALabs = "MedicareProject"
  }
}



resource "aws_iam_policy" "github_apply_policy" {
  
  name = "github_apply_policy"

  policy= jsonencode({
    
    Version: "2012-10-17",
    
    Statement: [
      {
        Sid = "S3BucketReadPermissions",
        
        Effect = "Allow",
        
        Action= [
          "s3:GetAccelerateConfiguration",
          "s3:GetBucketAcl",
          "s3:GetBucketCORS",
          "s3:GetBucketLogging",
          "s3:GetBucketObjectLockConfiguration",
          "s3:GetBucketPolicy",
          "s3:GetBucketPublicAccessBlock",
          "s3:GetBucketRequestPayment",
          "s3:GetBucketTagging",
          "s3:GetBucketVersioning",
          "s3:GetBucketWebsite",
          "s3:GetEncryptionConfiguration",
          "s3:GetLifecycleConfiguration",
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ],

        Resource = [
          "arn:aws:s3:::medicare-pipeline-tf-state-cjk-2026",
          "arn:aws:s3:::medicare-cms-data-cjk-2026"
        ]
      },
      {
        Sid = "S3ObjectReadWritePermissions",
        
        Effect = "Allow",
        
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ],
        
        Resource = [
          "arn:aws:s3:::medicare-pipeline-tf-state-cjk-2026/*",
          "arn:aws:s3:::medicare-cms-data-cjk-2026/*"
        ]
      },
      {
        Sid = "Ec2SSMDescribePermissions",
        
        Effect = "Allow",
        
        Action= [
          "ec2:DescribeInstances",
          "ec2:DescribeInstanceStatus",
          "ssm:DescribeInstanceInformation",
        ],

        Resource = "*"
      },
      {
        "Effect":"Allow",
        "Action":"ssm:SendCommand",
        "Resource":[
            "arn:aws:ec2:us-east-1:440107864885:instance/*",
            "arn:aws:ssm:us-east-1:440107864885:document/AWS-RunShellScript"
        ]
      },     
      {
        Sid = "GitHubECRTokenPermissions"
        
        Effect = "Allow"
        
        Action = ["ecr:GetAuthorizationToken"]
        
        Resource = "*"
      },
      {
        Sid = "GitHubECRPushPermissions"
        
        Effect = "Allow"
        
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage"
        ]
        
        Resource = aws_ecr_repository.cms_proj_streamlit.arn
      },
      {
        "Sid": "ECSExpressModeManagement",
        
        "Effect": "Allow",
        
        "Action": [
          "ecs:CreateExpressGatewayService",
          "ecs:UpdateExpressGatewayService",
          "ecs:DeleteExpressGatewayService",
          "ecs:DescribeServices",
          "ecs:ListServices"
        ],
        
        "Resource": "arn:aws:ecs:*:*:service/*/*"
      },
      {
        "Sid": "AllowPassRolesToECSExpress",
        
        "Effect": "Allow",
        
        "Action": [
          "iam:PassRole"
        ],
        
        "Resource": [
          "arn:aws:iam::*:role/ecs_streamlit_s3_role",
          "arn:aws:iam::*:role/ecs_streamlit_ecr_role",
          "arn:aws:iam::*:role/ecs_express_infra_role"
        ],

        "Condition": {
          
          "StringEquals": {
            "iam:PassedToService": [
              "ecs.amazonaws.com",
              "ecs-tasks.amazonaws.com",
              "express.ecs.amazonaws.com"
            ]
          }
        }
      }
    ]
  })

  tags= {
    DEALabs = "MedicareProject"
  }
}



resource "aws_iam_policy" "github_build_policy" {
  
  name = "github_build_policy"

  policy= jsonencode({
    
    Version: "2012-10-17",
    
    Statement: [
      {
        Sid = "EC2StartStopPermissions",
        
        Effect = "Allow",
        
        Action= [
          "ec2:StartInstances",
          "ec2:StopInstances"
        ],

        Resource = aws_instance.airflow_host.arn
      },

      {
        Sid = "Ec2SSMDescribePermissions",
        
        Effect = "Allow",
        
        Action= [
          "ec2:DescribeInstances",
          "ec2:DescribeInstanceStatus",
          "ssm:DescribeInstanceInformation",
        ],

        Resource = "*"
      },

      {
        Sid = "SSMStartStopResumeSessionPermission",
        
        Effect = "Allow",
        
        Action = [
          "ssm:StartSession",
          "ssm:TerminateSession",
          "ssm:ResumeSession"
        ],
        
        Resource = [
          aws_instance.airflow_host.arn,
          "arn:aws:ssm:us-east-1:440107864885:document/AWS-StartPortForwardingSession"
        ]
      },

      {
        Sid = "RunLambdaFunctions",
        
        Effect = "Allow",
        
        Action= [
          "lambda:InvokeFunction"
        ],

        Resource = aws_lambda_function.move_gdrive_files_to_s3.arn
      },

      {
        Sid = "SSMGetParameterPermission",
        
        Effect = "Allow",
        
        Action = [
          "ssm:GetParameter"
        ],
        
        Resource = "arn:aws:ssm:us-east-1:440107864885:parameter/medicare-pipeline/*"
      },

      {
        Sid = "SecretsManagerSessionPermission",
        
        Effect = "Allow",
        
        Action = [
          "secretsmanager:GetSecretValue",
        ],
        
        Resource = aws_secretsmanager_secret.airflow_api_creds.arn
      }            
    ]
  })

  tags= {
    DEALabs = "MedicareProject"
  }
}



resource "aws_iam_role_policy_attachment" "github_dev_env_plan_policy_attachment"{
  
  role = aws_iam_role.github_plan_role_dev.name
  
  policy_arn = aws_iam_policy.github_dev_env_plan_policy.arn
} 



resource "aws_iam_role_policy_attachment" "github_apply_role_policy_attachment"{
  
  role = aws_iam_role.github_apply_role.name
  
  policy_arn = aws_iam_policy.github_apply_policy.arn
} 



resource "aws_iam_role_policy_attachment" "github_build_policy_attachment"{
  
  role = aws_iam_role.github_build_role.name
  
  policy_arn = aws_iam_policy.github_build_policy.arn
} 






