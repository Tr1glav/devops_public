# temporal_standalone

Устанавливает [Temporal](https://temporal.io/) server standalone: бинарник, SQLite-БД, CLI, systemd. Опционально — воркеры: Python (venv + `worker.py`) и Java (jar + JRE 17).

## Использование

```yaml
- hosts: temporal
  become: true
  roles:
    - temporal_standalone
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `temporal_version` | `1.29.3` | Версия сервера |
| `arch` | `amd64` | Архитектура |
| `temporal_user` / `temporal_group` | `temporal` | Системный пользователь/группа |
| `bin_dir` | `/usr/local/bin` | Каталог бинарников |
| `data_dir` / `config_dir` | `/var/lib/temporal` / `/etc/temporal` | Данные и конфиг |
| `db_file` | `{{ data_dir }}/temporal.db` | Файл SQLite-БД |
| `temporal_cli_url` | GitHub releases (CLI 1.2.0) | Откуда качать CLI |
| `install_python_worker` | `true` | Ставить Python-воркер |
| `python_venv_dir` / `python_worker_script` | `/opt/temporal-worker/venv` / `worker.py` | Python-воркер |
| `install_java_worker` | `false` | Ставить Java-воркер |
| `worker_jar_url` / `worker_jar_dest` | `""` / `/opt/temporal-worker/worker.jar` | Java-воркер |

## Примечания

- Для Python-воркера обязателен `python_worker_script` (свой код).
- Java-воркер требует `worker_jar_url` с реальным адресом.
