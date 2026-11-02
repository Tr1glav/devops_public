# postgres

Поднимает PostgreSQL 16 с HA-стэком: **Patroni** (оркестрация, REST API на 8008) + **pgbouncer** (пул соединений, порт 6432). Приложение-БД и пользователи создаются по описанию из Vault.

## Использование

```yaml
- hosts: postgres
  become: true
  roles:
    - postgres
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `postgres_version` | `16` | Версия PostgreSQL |
| `cluster_name` | `postgres-cluster` | Имя кластера |
| `postgres_conf` | max_connections=100, shared_buffers=1GB, work_mem=16MB | Параметры postgresql |
| `pg_hba_conf` | local/loopback trust, remote md5 | Правила доступа |
| `system_users` | `('postgres','replicator','admin')` | Системные пользователи |
| `patroni_version` | `2.1.4` | Версия Patroni |
| `patroni_cluster_name` | `postgres-cluster` | Имя кластера Patroni |
| `patroni_restapi_port` | `8008` | Порт REST API |
| `patroni_home` | `/var/lib/patroni` | Каталог Patroni |
| `venv_path` | `/opt/patroni-venv` | venv для Patroni |
| `pgbouncer_port` | `6432` | Порт pgbouncer |
| `pgbouncer_pool_mode` | `transaction` | Режим пула |
| `pgbouncer_pool_size` / `pgbouncer_default_pool_size` | `25` / `20` | Размер пулов |
| `pgbouncer_max_client_conn` | `100` | Макс. соединений на клиент |
| `pgbouncer_databases` | postgres → `{{ patroni_cluster_name }}-leader` | БД в pgbouncer |
| `vault_mount` / `vault_path` | `infra` / `{{ env }}/postgres/appdb` | Секреты приложения в Vault |
| `vault_dbs_path` / `vault_users_path` | `.../appdb/dbs`, `.../appdb/users` | Описания БД и пользователей |

## Примечания

- `vault_addr`/`vault_token` берутся из env (`VAULT_ADDR`, `VAULT_TOKEN`).
- Клиенты подключаются через pgbouncer (6432) или напрямую (5432).
- Хендлеры: `Stop and disable postgresql`, `Restart patroni`, `Reload systemd and restart patroni`, `Restart pgbouncer`.
