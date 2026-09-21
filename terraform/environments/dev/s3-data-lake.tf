resource "aws_s3_bucket" "medicare_s3_data_lake" {
  
  bucket = "medicare-cms-data-cjk-2026"
}



resource "aws_s3_bucket_versioning" "medicare_s3_data_lake" {
  
  bucket = aws_s3_bucket.medicare_s3_data_lake.id
  
  versioning_configuration {
    
    status = "Enabled"
  }
}



resource "aws_s3_bucket_server_side_encryption_configuration" "medicare_s3_data_lake" {
  bucket = aws_s3_bucket.medicare_s3_data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



resource "aws_s3_bucket_public_access_block" "medicare_s3_data_lake" {
  bucket = aws_s3_bucket.medicare_s3_data_lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true  
}

