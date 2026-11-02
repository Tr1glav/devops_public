# vault_k8s

Разворачивает [HashiCorp Vault](https://www.vaultproject.io/) в k3s-кластере через официальный Helm-чарт: standalone или HA (raft), UI, опционально injector.

## Использование

```yaml
- hosts: k3s-server
  become: true
  roles:
    - vault_k8s
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `vault_k8s_release_name` / `vault_k8s_namespace` | `vault` | Release и namespace |
| `vault_k8s_helm_version` | `0.32.0` | Версия Helm-чарта |
| `vault_k8s_vault_version` | `1.21.2` | Версия Vault |
| `vault_k8s_mode` | `standalone` | `standalone` или `ha` |
| `vault_k8s_storage_backend` | `raft` | Бэкенд хранения |
| `vault_k8s_storage_size` / `vault_k8s_storage_class` | `10Gi` / `""` | Том (default — local) |
| `vault_k8s_ha_replicas` | `3` | Реплики в HA-режиме |
| `vault_k8s_service_type` | `ClusterIP` | Тип сервиса |
| `vault_k8s_unseal_method` | `shamir` | Метод unseal |
| `vault_k8s_ui_enabled` | `true` | Включить UI |
| `vault_k8s_injector_enabled` | `false` | Secrets injector |
| `vault_k8s_tls_disable` | `true` | Отключить TLS (за haproxy) |
| `vault_k8s_resources` | 256Mi/250m | Лимиты ресурсов |
| `vault_k8s_extra_values` | `{}` | Доп. values для чарта |

## Примечания

- Kubeconfig: `/etc/rancher/k3s/k3s.yaml` (роль `k3s`).
- Bare-metal вариант — роль `vault`.
