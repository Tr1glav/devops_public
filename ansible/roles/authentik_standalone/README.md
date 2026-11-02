# authentik_standalone

Разворачивает [Authentik](https://goauthentik.io/) (SSO/IdP) standalone на одном хосте: PostgreSQL, Redis, nginx-фронт и сам authentik. Секреты (secret key, пароль БД) — из Vault, SSL-сертификат — из mounts `certs`.

## Использование

```yaml
- hosts: authentik
  become: true
  roles:
    - authentik_standalone
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `authentik_version` | `2025.10.3` | Версия Authentik |
| `authentik_domain` | `auth.{{ domain }}` | Домен для сертификата и почты |
| `authentik_install_dir` | `/opt/authentik` | Каталог установки |
| `authentik_db_name` / `authentik_db_user` | `authentik` | БД PostgreSQL |
| `authentik_db_host` / `authentik_db_port` | `localhost` / `5432` | Адрес БД |
| `authentik_db_password` | `""` | Пароль БД (из Vault) |
| `authentik_redis_host` / `authentik_redis_port` | `localhost` / `6379` | Redis |
| `authentik_email_host` / `authentik_email_port` | `{{ smtp_host }}` / `587` | SMTP для писем |
| `authentik_email_from` | `authentik@{{ authentik_domain }}` | Отправитель |
| `authentik_vault_mount` / `authentik_vault_path` | `infra` / `{{ env }}/authentik` | Секреты в Vault |
| `authentik_enable_ssl` | `true` | Включить TLS на nginx |
| `authentik_certs_vault_mount` / `authentik_certs_vault_path` | `certs` / `{{ env }}/{{ authentik_domain }}` | Сертификат в Vault |
| `authentik_listen_port` | `9000` | Порт самого authentik |
| `authentik_trusted_proxy_cidrs` | `10/8, 172.16/12, 192.168/16` | Доверенные прокси (X-Forwarded-For) |

## Примечания

- Требуется переменная окружения `domain` (group_vars).
- `smtp_host` — общая переменная SMTP-сервера (group_vars).
