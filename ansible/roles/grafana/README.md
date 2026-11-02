# grafana

Устанавливает [Grafana OSS](https://grafana.com/oss/grafana/) бинарником: пользователь, конфиг, datasource (по умолчанию Prometheus на `localhost:9090`), дашборды, systemd-сервис.

## Использование

```yaml
- hosts: monitoring
  become: true
  roles:
    - grafana
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `grafana_version` | `11.2.0` | Версия Grafana |
| `grafana_port` | `3000` | Порт веб-интерфейса |
| `grafana_admin_user` | `admin` | Админский пользователь |
| `grafana_dir` / `grafana_config_dir` | `/opt/grafana` / `/etc/grafana` | Каталог и конфиг |
| `grafana_url` | `dl.grafana.com` | Откуда качать архив |
| `grafana_datasources` | Prometheus (default) | Список datasource'ов |
| `grafana_dashboards` | system-overview, node-overview | Дашборды для развёртывания |

## Примечания

- Пароль админа задаётся в group_vars/Vault (не в defaults).
- Хендлер: `Restart grafana`.
