

resource "aws_secretsmanager_secret" "airflow_api_creds" {
  name = "medicare-cms/airflow_api_creds"
  description = "Container that will point to credentials needed to access airflow."

  tags= {
    DEALabs = "MedicareProject"
  }
}


data "aws_secretsmanager_secret" "gdrive_file_secret"{
  name = "medicare_roject_gdrive_credentials"
}
