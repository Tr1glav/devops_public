# vm/node_exporter

Устанавливает [node_exporter](https://github.com/prometheus/node_exporter) (бинарник, качается через github-cache): системный пользователь, systemd-сервис, метрики для Prometheus.

## Использование

```yaml
- hosts: all
  become: true
  roles:
    - vm/node_exporter
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `node_exporter_version` | `1.10.2` | Версия node_exporter |
| `node_exporter_user` / `node_exporter_group` | `node_exporter` | Системный пользователь/группа |
| `node_exporter_dir` | `/opt/node_exporter` | Каталог бинарника |
| `node_exporter_url` | github-cache URL | Откуда качать бинарник |

## Примечания

- Хендлер: `Restart node_exporter`.
- Prometheus подхватывает ноды через сгенерированные targets (роль `prometheus`).
