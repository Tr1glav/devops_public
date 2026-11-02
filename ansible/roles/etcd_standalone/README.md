# etcd_standalone

Устанавливает [etcd](https://etcd.io/) standalone: бинарник (качается через github-cache), системный пользователь, конфиг, проверка кластера.

## Использование

```yaml
- hosts: etcd
  become: true
  roles:
    - etcd_standalone
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `etcd_version` | `3.5.9` | Версия etcd |
| `etcd_cluster_name` | `etcd-cluster` | Имя кластера |
| `etcd_client_port` | `2379` | Порт клиентов |
| `etcd_peer_port` | `2380` | Порт пиров |
| `etcd_url` | github-cache URL | Откуда качать бинарник |

## Примечания

- Хендлеры: `Reload systemd`, `Restart etcd`, `Reload systemd and restart etcd`.
