terraform {
  required_version = ">= 1.0.0"

  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "0.46.4"
    }
    vault = {
      version = "~> 4.8.0"
    }
  }
}
provider "vault" {
  address = var.vault_addr
  token   = var.vault_token
}
provider "proxmox" {
  # Основные параметры подключения
  endpoint  = data.vault_kv_secret_v2.hypervisor.data["pm_api_url"]
  api_token = "${data.vault_kv_secret_v2.hypervisor.data["pm_api_token_id"]}=${data.vault_kv_secret_v2.hypervisor.data["pm_api_token_secret"]}"
  insecure  = true # Аналог pm_tls_insecure
  # Логирование (аналог pm_debug/pm_log_enable)
  tmp_dir = "/tmp/terraform-proxmox" # Директория для временных файлов
}

