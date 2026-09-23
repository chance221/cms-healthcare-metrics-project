###Infra for hosting Streamlit App###

variable "streamlit_image_tag" {
  description = "ECR image tag for the Streamlit container. A unique tag per build (e.g. prod-<git-sha>) is what makes Terraform detect a real change and trigger a new ECS deployment -- pushing a new image under a static tag like 'latest' does not."
  type        = string
  default     = "latest"
}



resource "aws_ecr_repository" "cms_proj_streamlit"{
  
  name = "cms-proj-streamlit"

  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}



resource "aws_ecr_lifecycle_policy" "app_repo_policy" {
  repository = aws_ecr_repository.cms_proj_streamlit.name
   policy = jsonencode({
    rules = [
      {
        rulePriority = 2
        description  = "Keep only the last 3 production images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["prod-"]
          countType     = "imageCountMoreThan"
          countNumber   = 3
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}



resource "aws_ecs_express_gateway_service" "streamlit_app" {
  
  service_name = "cms-proj-streamlit"

  cluster = "default"

  execution_role_arn = aws_iam_role.ecs_streamlit_ecr_role.arn
  
  task_role_arn  = aws_iam_role.ecs_streamlit_s3_role.arn
  
  infrastructure_role_arn = aws_iam_role.ecs_express_infra_role.arn
  
  primary_container {
    image          = "${aws_ecr_repository.cms_proj_streamlit.repository_url}:${var.streamlit_image_tag}"
    container_port = 8080 
  }
  
  cpu = "1024" # 1 vCPU
  memory = "2048" # 2 GB

  scaling_target  {
    min_task_count = 1
    max_task_count = 3
    auto_scaling_metric = "AVERAGE_CPU"
    auto_scaling_target_value = 70
  }

  depends_on = [
    aws_iam_role_policy_attachment.ecs_streamlit_s3_policy_attachment,
    aws_iam_role_policy_attachment.ecs_streamlit_ecr_access_policy_attachment,
    aws_iam_role_policy_attachment.ecs_express_infra_attach
  ]
}


output "streamlit_url_object" {
  value       = aws_ecs_express_gateway_service.streamlit_app.ingress_paths[0].endpoint
  description = "The public URL hosting the Streamlit web application."
}



