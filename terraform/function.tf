data "archive_file" "function_packer" {
  output_path = "${path.module}/billfunc.zip"
  source_file = "../main.py"
  type        = "zip"
}


resource "yandex_function" "billfunc" {
  name               = "fn-billing-loader"
  description        = "serverless function Serverless Function to load Yandex.Cloud billing data to ClickHouse"
  user_hash          = "any_user_defined_string"
  runtime            = "python37-preview"
  entrypoint         = "main.handler"
  memory             = "512"
  execution_timeout  = "360"
  service_account_id = yandex_iam_service_account.sa_billing_mngr.id
  tags               = ["yandex-billing-loader"]
  content {
    zip_filename = "../dist.zip"
  }
  environment        = {
    CH_HOST         = "${module.managed-clickhouse-billing-cluster.cluster_hosts_fqdns[0]}"    
    CH_PASSWORD     = "${module.managed-clickhouse-billing-cluster.cluster_users_passwords["billing_db_user"]}"
    CH_DB           = "yc-billing"
    CH_USER         = "billing_db_user"
    CH_TABLE        = "yc_billing_export"
    STORAGE_BUCKET  = var.storage_bucket
    STORAGE_FOLDER  = var.storage_folder
    AWS_ACCESS_KEY_ID = var.aws_access_key_id
    AWS_SECRET_ACCESS_KEY = var.aws_secret_access_key
  }
  depends_on     = [yandex_resourcemanager_folder_iam_member.invoker-svc-iam]
}

resource "yandex_function_trigger" "billfunc_trigger" {
    name        = "fn-billing-loader-trigger"
    description = "fn-billing-loader hourly timer"
    timer {
        cron_expression = "0 * ? * * *"
    }
    function  {
        id = yandex_function.billfunc.id
        service_account_id = yandex_iam_service_account.sa_billing_mngr.id
  }
}

