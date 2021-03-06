module "billing-vpc" {
  source       = "./vpc"
  network_name = "billing-network"
  subnets = {
    "billing-data-subnet" : {
      zone           = var.yc_main_zone
      v4_cidr_blocks = ["10.0.1.0/24"]
    }
  }
}

module "managed-clickhouse-billing-cluster" {

  source       = "./mdb-clickhouse"
  cluster_name = "managed_clickhouse_billing_cluster"
  network_id   = module.billing-vpc.vpc_network_id
  description  = "Billing analytics ClickHouse database"
  labels = {
    env        = "testing"
    deployment = "terraform"
  }
  #environment = "PRESTABLE"

  resource_preset_id = "s2.micro" #s2.small
  disk_size          = 50 #GiB
  disk_type_id       = "network-ssd"

  hosts = [
    {
      zone           = var.yc_main_zone,
      subnet_id        = module.billing-vpc.subnet_ids_by_names["billing-data-subnet"]
      assign_public_ip = true
      shard_name       = "billing1"
    }
  ]
   databases = [
    {
      name  = var.billing_db_name
      owner = "billing_db_user"
    }
  ]
  users = [
    {
      name     = "billing_db_user"
      password = random_password.password.result
    }
  ]
  user_permissions = {
    "billing_db_user" : [
      {
        database_name = var.billing_db_name
      }
    ]}
}