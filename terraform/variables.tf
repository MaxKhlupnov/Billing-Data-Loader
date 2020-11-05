variable "yc_oauth_token" {
  description = "YC OAuth token"
  default     = ""
  type        = string
}

variable "yc_cloud_id" {
  description = "ID of a cloud"
  default     = ""
  type        = string
}

variable "yc_folder_id" {
  description = "ID of a folder"
  default     = ""
  type        = string
}

variable "yc_main_zone" {
  description = "The main availability zone"
  default     = "ru-central1-a"
  type        = string
}

variable "billing_db_name" {
  description = "Clickhouse database name for storing billing records"
  default     = "yc-billing"
  type        = string
}

variable "storage_bucket" {
  description = "Yandex object storage Bucket importing from"
  default     = "billing-info"
  type        = string
}

variable "storage_folder" {
  description = "Folder name inside bucket (usually it is yc-billing-export or yc-billing-export-with-resources)"
  default     = "yc-billing-export"
  type        = string
}

variable "aws_access_key_id" {
    description = "AWS Access Key for Yandex Object storage"
    default     = ""
    type        = string
}

variable "aws_secret_access_key" {
    description = "Aws Access Secret Key for Yandex Object storage"
    default     = ""
    type        = string
}