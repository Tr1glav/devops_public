# k3s

Устанавливает [k3s](https://k3s.io/) (server или agent): flannel `wireguard-native`, отключены traefik/servicelb/local-storage. На server-нодах дополнительно настраивает firewall (iptables + iptables-persistent) для портов Kubernetes и показывает kubeconfig.

## Использование

```yaml
- hosts: k3s-server
  become: true
  roles:
    - k3s
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `k3s_version` | `v1.32.3+k3s1` | Версия k3s |
| `k3s_mode` | `server` | `server` или `agent` |
| `k3s_server_ip` | `{{ ansible_host }}` | URL/адрес сервера для агентов |
| `k3s_tls_san` | `[]` | Дополнительные SAN для сертификата |
| `k3s_disabled_components` | `traefik, servicelb, local-storage` | Отключаемые компоненты |
| `k3s_flannel_backend` | `wireguard-native` | Бэкенд флани |
| `k3s_cluster_cidr` / `k3s_service_cidr` | `10.42.0.0/16` / `10.43.0.0/16` | CIDR подсетей |
| `k3s_cluster_name` | `{{ env }}` | Имя кластера |
| `k3s_data_dir` | `/var/lib/rancher/k3s` | Каталог данных |
| `k3s_write_kubeconfig` | `true` | Копировать kubeconfig в `/etc/rancher/k3s/k3s.yaml` |
| `k3s_firewall_ports` | 6443, 10250, 8472/udp, 2379, 2380 | Порты, открываемые firewall'ом (только server) |

## Примечания

- Kubeconfig по умолчанию: `/etc/rancher/k3s/k3s.yaml` (используется ролями `awx_k8s`, `vault_k8s`).
- Traefik отключён — публикация сервисов через NodePort + haproxy.
- Хендлер: `Restart k3s`.
