###Infra for hosting Airflow Instance###

data "aws_vpc" "default"{
  default= true
}



data "aws_subnets" "default_subnets"{
  filter{
    
    name = "vpc-id"
    
    values = [data.aws_vpc.default.id]
  }  
}



data "aws_ami" "amazon_linux_2023" {
  
  most_recent = true
  
  owners      = ["amazon"]

  filter {
    
    name   = "name"
    
    values = ["al2023-ami-2023.*-kernel-6.1-x86_64"]
  }
}



data "archive_file" "airflow_bundle_zip" {
  
  type        = "zip"
  
  output_path = "${path.module}/airflow-bundle.zip"

  dynamic "source" {
    
    for_each = fileset("${path.module}/../../../pyspark_jobs", "**/*.py")
    
    content {
      
      filename = "pyspark_jobs/${source.value}"
      
      content  = file("${path.module}/../../../pyspark_jobs/${source.value}")
    }
  }  

  dynamic "source" {
    
    for_each = fileset("${path.module}/../../../configs", "**/*.{yaml,yml}")
    
    content {
      
      filename = "configs/${source.value}"
      
      content  = file("${path.module}/../../../configs/${source.value}")
    }
  }  
  
  dynamic "source" {
    for_each = fileset("${path.module}/../../../dags", "**/*.py")
    content {
      filename = "dags/${source.value}"
      content  = file("${path.module}/../../../dags/${source.value}")
    }
  }
}



resource "aws_s3_object" "airflow_bundle_upload" {
  
  bucket = aws_s3_bucket.cms_proj_python_scripts.id
  
  key    = "airflow-bundle.zip"
  
  source = data.archive_file.airflow_bundle_zip.output_path
  
  etag   = data.archive_file.airflow_bundle_zip.output_md5
}



resource "aws_security_group" "ec2_airflow_sg" {
  
  name = "ec2_airflow_sg"
  
  description = "No inbound access -- reachable only via SSM. Outbound HTTPS only, for AWS API calls."
  
  vpc_id = data.aws_vpc.default.id

  egress {
    
    description = "HTTPS to AWS APIs (SSM tunnel, S3, Glue, Lambda, STS)"
    
    from_port = 443
    
    to_port = 443
    
    protocol = "tcp"
    
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    DEALabs = "MedicareProject"
  }
}


resource "aws_instance" "airflow_host" {
  
  ami = data.aws_ami.amazon_linux_2023.id
  
  instance_type = "t3.medium" 

  subnet_id = data.aws_subnets.default_subnets.ids[0]
  
  vpc_security_group_ids = [aws_security_group.ec2_airflow_sg.id]

  iam_instance_profile = aws_iam_instance_profile.ec2_airflow_profile.name 
 
  root_block_device {
    
    volume_size = 30 
    
    volume_type = "gp3"
    
    encrypted = true
    
    delete_on_termination = true
  }

  user_data = templatefile("${path.module}/airflow_user_data.sh.tpl", {
    
    code_bucket = aws_s3_bucket.cms_proj_python_scripts.id
    
    code_key = "airflow-bundle.zip"
  })

  user_data_replace_on_change = true

  tags = {
    Name        = "airflow-production-host"
    
    Environment = "production"
    
    Application = "Apache-Airflow"
    
    DEALabs = "MedicareProject"
  }
}


output "airflow_instance_id" {

  value = aws_instance.airflow_host.id
}



resource "aws_ssm_parameter" "airflow_instance_id" {

  name = "/medicare-pipeline/airflow_instance_id"

  type = "String"

  value = aws_instance.airflow_host.id

  tags = {
    DEALabs = "MedicareProject"
  }
}