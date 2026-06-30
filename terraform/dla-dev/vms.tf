locals {
  node_template_map = {
    "pve-1" = 9001
    "pve-2" = 9002
  }
}

resource "proxmox_virtual_environment_vm" "cloudinit" {
  for_each  = var.cloudinit_vms
  name      = each.key
  node_name = each.value.node
  tags      = concat(["terraform"], lookup(each.value, "tags", []))

  # Ресурсы CPU/Memory
  cpu {
    cores   = each.value.cores
    sockets = each.value.sockets
    type    = "host"
  }

  clone {
    vm_id     = local.node_template_map[each.value.node]
    node_name = each.value.node
    full      = true
    retries   = 6
  }

  memory {
    dedicated = each.value.memory
    floating  = each.value.float_memory
  }

  # Диск
  disk {
    datastore_id = "local-lvm"
    interface    = "scsi0"
    size         = each.value.disk_size
    file_format  = "raw"
  }

  # Сетевые интерфейсы
  dynamic "network_device" {
    for_each = toset(each.value.networks)
    content {
      bridge = network_device.value[0]
      model  = "virtio"
    }
  }

  # Cloud-init
  initialization {
    datastore_id = "local-lvm"
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
      username = data.vault_kv_secret_v2.svc-init.data["username"]
      password = data.vault_kv_secret_v2.svc-init.data["user_password"]
      keys     = [data.vault_kv_secret_v2.svc-init.data["public_key"]]
    }
  }

  agent {
    enabled = true
  }

  serial_device {}

  on_boot = true
  startup {
    order      = 1
    up_delay   = 60
    down_delay = 60
  }

  operating_system {
    type = "l26"
  }

  dynamic "usb" {
    for_each = lookup(each.value, "usb", [])
    content {
      host = usb.value
      usb3 = false
    }
  }

  lifecycle {
    ignore_changes = [
      vm_id,
      clone,
      initialization,
      tags,
      disk,
      network_device,
      usb, # Добавляем usb в ignore_changes чтобы изменения USB не вызывали пересоздание
    ]
  }
}