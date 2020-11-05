resource "yandex_iam_service_account" "sa_billing_mngr" {
  name        = "svc-billing-mngr"
  description = "service account to work with billing loader functoion"
}

resource "yandex_resourcemanager_folder_iam_member" "invoker-svc-iam" {
  folder_id          = var.yc_folder_id
  role               = "serverless.functions.invoker"
  member             = "serviceAccount:${yandex_iam_service_account.sa_billing_mngr.id}"
}