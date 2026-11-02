variable "containers" {
  default = {
    "cache-server-1" = { node = "pve-2", tags = ["cache-server"], networks = [["vmbr1", "<hidden-ip>/16", "<hidden-ip>"]], cores = 2, memory = 1024, size = 60, unprivileged = true }
    "torserver"      = { node = "pve-1", tags = ["torserver"], networks = [["vmbr0", "<hidden-ip>/23", "<hidden-ip>"]], cores = 4, memory = 4096, size = 8, unprivileged = true }
    "ansible-1"      = { node = "pve-2", tags = ["ansible"], networks = [["vmbr1", "<hidden-ip>/16", "<hidden-ip>"]], cores = 2, memory = 512, size = 8, unprivileged = true }
    "vault-1-ha"     = { node = "pve-2", tags = ["vault"], networks = [["vmbr1", "<hidden-ip>/16", "<hidden-ip>"]], cores = 2, memory = 512, size = 8, unprivileged = true }
    "vault-2-ha"     = { node = "pve-2", tags = ["vault"], networks = [["vmbr1", "<hidden-ip>/16", "<hidden-ip>"]], cores = 2, memory = 512, size = 8, unprivileged = true }
    "vault-3-ha"     = { node = "pve-2", tags = ["vault"], networks = [["vmbr1", "<hidden-ip>/16", "<hidden-ip>"]], cores = 2, memory = 512, size = 8, unprivileged = true }
    "certbot-1"      = { node = "pve-2", tags = ["certbot"], networks = [["vmbr1", "<hidden-ip>/16", "<hidden-ip>"]], cores = 2, memory = 512, size = 8, unprivileged = true }
    "prometheus-1"   = { node = "pve-2", tags = ["prometheus"], networks = [["vmbr1", "<hidden-ip>/16", "<hidden-ip>"]], cores = 2, memory = 512, size = 8, unprivileged = true }
    "haproxy-1"      = { node = "pve-1", tags = ["haproxy"], networks = [["vmbr1", "<hidden-ip>/16", "<hidden-ip>"]], cores = 1, memory = 512, size = 8, unprivileged = true }
    "haproxy-2"      = { node = "pve-2", tags = ["haproxy"], networks = [["vmbr1", "<hidden-ip>/16", "<hidden-ip>"]], cores = 1, memory = 512, size = 8, unprivileged = true }
  }
}
variable "cloudinit_vms" {
  default = {
    "vpn-connector-1" = { node = "pve-1", tags = ["vpn-connector"], cores = 2, sockets = 1, memory = 2048, float_memory = 1024, disk_size = 30, networks = [["vmbr1", "<hidden-ip>/16", "<hidden-ip>"]] }
    "wh-list-1"       = { node = "pve-1", tags = ["wh-list"], cores = 4, sockets = 1, memory = 4096, float_memory = 1024, disk_size = 30, networks = [["vmbr1", "<hidden-ip>/16", "<hidden-ip>"]] }
  }
}

variable "vault_addr" {
  description = "Адрес сервера Vault"
  type        = string
  default     = "http://localhost:8200" # Значение по умолчанию
}

variable "vault_token" {
  description = "Токен аутентификации Vault"
  type        = string
  sensitive   = true
}
