
resource "proxmox_virtual_environment_container" "lxc" {
  for_each  = var.containers
  node_name = each.value.node

  # Основные параметры
  tags         = concat(["terraform"], lookup(each.value, "tags", []))
  unprivileged = each.value.unprivileged
  # Ресурсы
  cpu {
    cores = each.value.cores
  }
  memory {
    dedicated = each.value.memory
  }

  # Диск
  disk {
    datastore_id = "local-lvm"
    size         = each.value.size # Число в GB
  }
  dynamic "network_interface" {
    for_each = toset(each.value.networks)
    content {
      name   = "eth0"
      bridge = network_interface.value[0]
    }
  }

  # Настройки сети через initialization
  initialization {
    hostname = each.key
    dns {
      servers = ["<hidden-ip>", "<hidden-ip>", "${cidrhost(each.value.networks[0][1], 1)}"]
      domain  = "${each.key}.dev.dla.su"
    }
    dynamic "ip_config" {
      for_each = each.value.networks
      content {
        ipv4 {
          address = ip_config.value[1]
          gateway = try(ip_config.value[2], null)
        }
      }
    }
    user_account {
      password = data.vault_kv_secret_v2.svc-init.data["user_password"]
      keys     = [data.vault_kv_secret_v2.svc-init.data["public_key"]]
    }
  }
  dynamic "features" {
    for_each = [1]
    content {
      nesting = true
      keyctl  = !each.value.unprivileged # keyctl только для привилегированных
    }
  }

  # Операционная система
  operating_system {
    template_file_id = "local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst"
    type             = "ubuntu" # Укажите ваш тип ОС
  }

  # Автозапуск
  start_on_boot = true
  started       = true
  lifecycle {
    ignore_changes = [
      vm_id,
      unprivileged,
      operating_system,
      initialization,
      vm_id,
      tags
    ]
  }

}