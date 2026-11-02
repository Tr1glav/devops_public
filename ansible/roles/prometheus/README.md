# prometheus

Устанавливает [Prometheus](https://prometheus.io/) бинарником (качается через github-cache): пользователь, конфиг, генерация targets, systemd-сервис.

## Использование

```yaml
- hosts: monitoring
  become: true
  roles:
    - prometheus
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `prometheus_version` | `2.51.2` | Версия Prometheus |
| `prometheus_user` / `prometheus_group` | `prometheus` | Системный пользователь/группа |
| `prometheus_dir` | `/opt/prometheus` | Каталог бинарника |
| `prometheus_config_dir` | `/etc/prometheus` | Каталог конфигов |
| `prometheus_refresh_interval` | `5m` | Периодичность обновления targets |
| `prometheus_url` | github-cache URL | Откуда качать бинарник |

## Примечания

- Targets генерируются из инвентаря (задача `generate_targets.yml`).
- Хендлеры: `Reload systemd`, `Enable and start prometheus`.
