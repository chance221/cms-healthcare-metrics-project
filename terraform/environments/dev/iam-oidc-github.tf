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
                "token.actions.githubusercontent.com:sub": "repo:chance221@39056884/cms-healthcare-metrics-project@1371657610:pull_request"
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
                "token.actions.githubusercontent.com:sub": "repo:chance221@39056884/cms-healthcare-metrics-project@1371657610:environment:production"
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
                "token.actions.githubusercontent.com:sub": "repo:chance221@39056884/cms-healthcare-metrics-project/workflows/deploy.yml@refs/heads/main"
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



resource "aws_iam_policy" "github_apply_storage_secrets_policy" {
  name = "github_apply_storage_secrets_policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
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
          "arn:aws:s3:::medicare-pipeline-tf-state-cjk-2026",
          "arn:aws:s3:::medicare-cms-data-cjk-2026",
          "arn:aws:s3:::cms-project-python-scripts-cjk-2026"
        ]
      },
      {
        Sid    = "S3ObjectReadWritePermissions"
        
        Effect = "Allow"
        
        Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:GetObjectTagging"]
        
        Resource = [
          "arn:aws:s3:::medicare-pipeline-tf-state-cjk-2026/*",
          "arn:aws:s3:::medicare-cms-data-cjk-2026/*",
          "arn:aws:s3:::cms-project-python-scripts-cjk-2026/*"
        ]
      },
      {
        Sid      = "SecretsManagerAirflowSecretPermissions"
        
        Effect   = "Allow"
        
        Action   = ["secretsmanager:CreateSecret", "secretsmanager:DescribeSecret", "secretsmanager:TagResource", "secretsmanager:DeleteSecret", "secretsmanager:GetResourcePolicy"]
        
        Resource = "arn:aws:secretsmanager:us-east-1:440107864885:secret:medicare-cms/airflow_api_creds-*"
      },
      {
        Sid      = "SecretsManagerGdriveSecretReadPermissions"
        
        Effect   = "Allow"
        
        Action   = ["secretsmanager:DescribeSecret", "secretsmanager:GetResourcePolicy"]
        
        Resource = "arn:aws:secretsmanager:us-east-1:440107864885:secret:medicare_roject_gdrive_credentials*"
      }
    ]
  })

  tags = {
    DEALabs = "MedicareProject"
  }
}

resource "aws_iam_policy" "github_apply_ec2_ssm_policy" {
  
  name = "github_apply_ec2_ssm_policy"

  policy = jsonencode({
    
    Version = "2012-10-17"
    
    Statement = [
      {
        Sid    = "EC2InstanceManagementPermissions"
        
        Effect = "Allow"
        
        Action = [
          "ec2:RunInstances", "ec2:TerminateInstances", "ec2:DescribeInstanceAttribute",
          "ec2:ModifyInstanceAttribute", "ec2:CreateTags", "ec2:DescribeTags",
          "ec2:CreateSecurityGroup", "ec2:DeleteSecurityGroup", "ec2:DescribeSecurityGroups",
          "ec2:AuthorizeSecurityGroupEgress", "ec2:RevokeSecurityGroupEgress"
          
        ]
        
        Resource = "*"
      },
      {
        Sid    = "Ec2SSMDescribePermissions"
        
        Effect = "Allow"
        
        Action = [
          "ec2:DescribeInstances", "ec2:DescribeInstanceStatus", "ssm:DescribeInstanceInformation",
          "ec2:DescribeImages", "ec2:DescribeVpcs", "ec2:DescribeVpcAttribute", "ec2:DescribeVolumes",
          "ec2:DescribeSubnets", "ec2:DescribeVpcs", "ec2:DescribeImages",
          "ec2:DescribeInstanceTypes", "ec2:DescribeInstanceCreditSpecifications"
        ]
        
        Resource = "*"
      },
      {
        Sid    = "SSMSendCommandPermission"
        
        Effect = "Allow"
        
        Action = "ssm:SendCommand"
        
        Resource = [
          "arn:aws:ec2:us-east-1:440107864885:instance/*",
          "arn:aws:ssm:us-east-1::document/AWS-RunShellScript"
        ]
      }
    ]
  })

  tags = {
    DEALabs = "MedicareProject"
  }
}

resource "aws_iam_policy" "github_apply_ecr_ecs_lambda_policy" {
  
  name = "github_apply_ecr_ecs_lambda_policy"

  policy = jsonencode({
    
    Version = "2012-10-17"
    
    Statement = [
      {
        Sid      = "GitHubECRTokenPermissions"
        
        Effect   = "Allow"
        
        Action   = ["ecr:GetAuthorizationToken"]
        
        Resource = "*"
      },
      {
        Sid    = "ECRRepositoryManagementPermissions"
        
        Effect = "Allow"
        
        Action = [
          "ecr:CreateRepository", "ecr:DescribeRepositories", "ecr:DeleteRepository",
          "ecr:TagResource", "ecr:PutImageTagMutability", "ecr:PutImageScanningConfiguration",
          "ecr:GetLifecyclePolicy", "ecr:PutLifecyclePolicy", "ecr:DeleteLifecyclePolicy",
          "ecr:ListTagsForResource"
        ]

        Resource = "arn:aws:ecr:us-east-1:440107864885:repository/cms-proj-streamlit"
      },
      {
        Sid    = "GitHubECRPushPermissions"
        
        Effect = "Allow"
        
        Action = [
          "ecr:BatchCheckLayerAvailability", "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart", "ecr:CompleteLayerUpload", "ecr:PutImage"
        ]
        Resource = aws_ecr_repository.cms_proj_streamlit.arn
      },
      {
        Sid    = "ECSExpressModeManagement"
        
        Effect = "Allow"
        
        Action = [
          "ecs:CreateExpressGatewayService", "ecs:UpdateExpressGatewayService",
          "ecs:DeleteExpressGatewayService", "ecs:DescribeExpressGatewayService",
          "ecs:DescribeServices", "ecs:ListServices"
        ]

        Resource = "arn:aws:ecs:*:*:service/*/*"
      },
      {
        Sid    = "ECSExpressTaskDefinitionManagement"

        Effect = "Allow"

        Action = [
          "ecs:RegisterTaskDefinition", "ecs:DescribeTaskDefinition",
          "ecs:DeregisterTaskDefinition"
        ]

        Resource = "arn:aws:ecs:*:*:task-definition/default-cms-proj-streamlit:*"
      },
      {
        Sid    = "LambdaFunctionManagementPermissions"
        
        Effect = "Allow"
        
        Action = [
          "lambda:CreateFunction", "lambda:GetFunction", "lambda:GetFunctionConfiguration",
          "lambda:UpdateFunctionCode", "lambda:UpdateFunctionConfiguration", "lambda:DeleteFunction",
          "lambda:TagResource", "lambda:ListVersionsByFunction", "lambda:GetFunctionCodeSigningConfig"
        ]
        
        Resource = "arn:aws:lambda:us-east-1:440107864885:function:move_gdrive_files_to_s3"
      },
      {
        Sid    = "LambdaLayerManagementPermissions"
        
        Effect = "Allow"
        
        Action = ["lambda:PublishLayerVersion", "lambda:GetLayerVersion", "lambda:DeleteLayerVersion", "lambda:ListLayerVersions"]
        
        Resource = [
          "arn:aws:lambda:us-east-1:440107864885:layer:google-api-dependencies",
          "arn:aws:lambda:us-east-1:440107864885:layer:google-api-dependencies:*"          
        ]
      }
    ]
  })

  tags = {
    DEALabs = "MedicareProject"
  }
}

resource "aws_iam_policy" "github_apply_iam_glue_policy" {
  
  name = "github_apply_iam_glue_policy"

  policy = jsonencode({
    
    Version = "2012-10-17"
    
    Statement = [
      {
        Sid    = "AllowPassRolesToECSExpress"
        
        Effect = "Allow"
        
        Action = ["iam:PassRole"]
        
        Resource = [
          "arn:aws:iam::*:role/ecs_streamlit_s3_role",
          "arn:aws:iam::*:role/ecs_streamlit_ecr_role",
          "arn:aws:iam::*:role/ecs_express_infra_role"
        ]
        
        Condition = {
          StringEquals = {
            "iam:PassedToService" = ["ecs.amazonaws.com", "ecs-tasks.amazonaws.com", "express.ecs.amazonaws.com"]
          }
        }
      },
      {
        Sid    = "GlueJobManagementPermissions"
        
        Effect = "Allow"
        
        Action = ["glue:CreateJob", "glue:GetJob", "glue:GetJobs", "glue:UpdateJob", "glue:DeleteJob", "glue:TagResource", "glue:GetTags"]
        
        Resource = [
          "arn:aws:glue:us-east-1:440107864885:job/cms_proj_raw_to_silver_glue_job",
          "arn:aws:glue:us-east-1:440107864885:job/cms_proj_silver_to_gold_glue_job"
        ]
      },
      {
        Sid    = "IAMRoleManagementPermissions"
        
        Effect = "Allow"
        
        Action = [
          "iam:CreateRole", "iam:GetRole", "iam:UpdateRole", "iam:UpdateAssumeRolePolicy",
          "iam:DeleteRole", "iam:TagRole", "iam:ListRolePolicies", "iam:ListAttachedRolePolicies",
          "iam:AttachRolePolicy", "iam:DetachRolePolicy"
        ]
        
        Resource = [
          "arn:aws:iam::440107864885:role/github_*",
          "arn:aws:iam::440107864885:role/cms_proj_*",
          "arn:aws:iam::440107864885:role/ecs_*",
          "arn:aws:iam::440107864885:role/ec2_airflow_*"
        ]
      },
      {
        Sid    = "IAMPolicyManagementPermissions"
        
        Effect = "Allow"
        
        Action = ["iam:CreatePolicy", "iam:GetPolicy", "iam:GetPolicyVersion", "iam:ListPolicyVersions", "iam:CreatePolicyVersion", "iam:DeletePolicyVersion", "iam:DeletePolicy", "iam:TagPolicy"]
        
        Resource = [
          "arn:aws:iam::440107864885:policy/github_*",
          "arn:aws:iam::440107864885:policy/cms_proj_*",
          "arn:aws:iam::440107864885:policy/ecs_*",
          "arn:aws:iam::440107864885:policy/ec2_airflow_*"
        ]
      },
      {
        Sid    = "IAMInstanceProfileManagementPermissions"
        
        Effect = "Allow"
        
        Action = ["iam:CreateInstanceProfile", "iam:GetInstanceProfile", "iam:DeleteInstanceProfile", "iam:AddRoleToInstanceProfile", "iam:RemoveRoleFromInstanceProfile", "iam:TagInstanceProfile"]
        
        Resource = "arn:aws:iam::440107864885:instance-profile/*"
      },
      {
        Sid      = "IAMOIDCProviderReadPermissions"
        
        Effect   = "Allow"
        
        Action   = ["iam:GetOpenIDConnectProvider"]
        
        Resource = "arn:aws:iam::440107864885:oidc-provider/token.actions.githubusercontent.com"
      },
      {
        "Sid": "AllowPassRoleToEC2Airflow",
        
        "Effect": "Allow",
        
        "Action": ["iam:PassRole"],
        
        "Resource": "arn:aws:iam::440107864885:role/ec2_airflow_role",
        
        "Condition": {
          
          "StringEquals": {
            "iam:PassedToService": "ec2.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = {
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



resource "aws_iam_role_policy_attachment" "github_apply_storage_secrets_attachment" {
  
  role       = aws_iam_role.github_apply_role.name
  
  policy_arn = aws_iam_policy.github_apply_storage_secrets_policy.arn
}



resource "aws_iam_role_policy_attachment" "github_apply_ec2_ssm_attachment" {
  
  role       = aws_iam_role.github_apply_role.name
  
  policy_arn = aws_iam_policy.github_apply_ec2_ssm_policy.arn
}



resource "aws_iam_role_policy_attachment" "github_apply_ecr_ecs_lambda_attachment" {
  
  role       = aws_iam_role.github_apply_role.name
  
  policy_arn = aws_iam_policy.github_apply_ecr_ecs_lambda_policy.arn
}



resource "aws_iam_role_policy_attachment" "github_apply_iam_glue_attachment" {
  
  role       = aws_iam_role.github_apply_role.name
  
  policy_arn = aws_iam_policy.github_apply_iam_glue_policy.arn
}



resource "aws_iam_role_policy_attachment" "github_build_policy_attachment"{
  
  role = aws_iam_role.github_build_role.name
  
  policy_arn = aws_iam_policy.github_build_policy.arn
} 






