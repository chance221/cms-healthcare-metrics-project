resource "aws_s3_bucket" "cms_proj_python_scripts" {
  bucket = "cms-project-python-scripts-cjk-2026"
}



resource "aws_s3_bucket_versioning" "cms_proj_python_scripts" {
  bucket = aws_s3_bucket.cms_proj_python_scripts.id
  versioning_configuration {
    status = "Enabled"
  }
}



resource "aws_s3_bucket_server_side_encryption_configuration" "cms_proj_python_scripts" {
  bucket = aws_s3_bucket.cms_proj_python_scripts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



resource "aws_s3_bucket_public_access_block" "cms_proj_python_scripts" {
  bucket = aws_s3_bucket.cms_proj_python_scripts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
  
}



