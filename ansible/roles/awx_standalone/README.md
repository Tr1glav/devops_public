# awx_standalone

Разворачивает [AWX](https://awx.readthedocs.io/) из исходников (git-тег) на барех-хосте/LXC: venv, uwsgi + daphne + wsrelay + dispatcher, receptor для удалённых инвентаризаций, nginx-фронт с SSL. БД — PostgreSQL, кэш/очередь — Redis.

> AWX разворачивается в LXC, контейнерный рантайм не ставится (`awx_install_podman: false`): веб/API/БД работают, но джобы и обновления проектов потребуют execution environment.

## Использование

```yaml
- hosts: awx
  become: true
  roles:
    - awx_standalone
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `awx_version` | `24.6.1` | Тег AWX в git |
| `awx_domain` | `awx.{{ domain }}` | Домен для сертификата и CSRF |
| `awx_install_dir` | `/opt/awx` | Каталог установки (source/ + venv/) |
| `awx_config_dir` / `awx_data_dir` | `/etc/tower` / `/var/lib/awx` | Конфиг и данные |
| `awx_db_name` / `awx_db_user` | `awx` | БД PostgreSQL |
| `awx_db_host` / `awx_db_port` / `awx_db_password` | `localhost` / `5432` / `""` | Адрес БД (пароль из Vault) |
| `awx_redis_host` / `awx_redis_port` | `localhost` / `6379` | Redis |
| `awx_uwsgi_port` / `awx_daphne_port` | `8052` / `8051` | Внутренние порты |
| `awx_listen_port` / `awx_ssl_port` | `80` / `443` | Порты nginx |
| `awx_enable_ssl` | `true` | TLS, сертификат из `certs` |
| `awx_admin_user` / `awx_admin_password` | `admin` / `""` | Админ (пароль из Vault) |
| `awx_receptor_version` / `awx_receptor_port` | `1.5.6` / `27199` | Receptor |
| `awx_install_podman` | `false` | Ставить podman для EE |
| `awx_node_type` / `awx_queue_name` | `hybrid` / `default` | Тип ноды и очередь |
| `awx_vault_mount` / `awx_vault_path` | `infra` / `{{ env }}/awx` | Секреты в Vault |
| `awx_certs_vault_mount` / `awx_certs_vault_path` | `certs` / `{{ env }}/{{ awx_domain }}` | Сертификат в Vault |

## Примечания

- Секреты (secret key, пароль БД, пароль admin) — из Vault `infra/<env>/awx`.
- Полный список сервисов — в `awx_services` (awx-uwsgi, awx-daphne, awx-wsrelay, awx-dispatcher, awx-callback-receiver, awx-receptor).
