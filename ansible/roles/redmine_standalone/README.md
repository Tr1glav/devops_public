# redmine_standalone

Устанавливает [Redmine](https://www.redmine.org/) 6: Ruby 3.3, PostgreSQL, Apache с SSL, SMTP. Секреты — из Vault.

## Использование

```yaml
- hosts: redmine
  become: true
  roles:
    - redmine_standalone
```

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `redmine_version` | `6.0.3` | Версия Redmine |
| `redmine_domain` | `redmine.{{ domain }}` | Домен |
| `redmine_install_dir` | `/var/lib/redmine` | Каталог установки |
| `redmine_user` | `www-data` | Пользователь Apache |
| `redmine_ruby_version` | `3.3.0` | Версия Ruby |
| `redmine_db_name` / `redmine_db_user` | `redmine` | БД PostgreSQL |
| `redmine_db_host` / `redmine_db_port` / `redmine_db_password` | `localhost` / `5432` / `""` | Адрес БД (пароль из Vault) |
| `redmine_listen_port` | `8080` | Внутренний порт Redmine |
| `redmine_enable_ssl` | `true` | TLS на Apache, сертификат из `certs` |
| `redmine_email_smtp_host` / `redmine_email_smtp_port` | `{{ smtp_host }}` / `587` | SMTP |
| `redmine_email_from` | `redmine@{{ redmine_domain }}` | Отправитель |
| `redmine_default_language` | `ru` | Язык по умолчанию |
| `redmine_vault_mount` / `redmine_vault_path` | `infra` / `{{ env }}/redmine` | Секреты в Vault |
| `redmine_certs_vault_mount` / `redmine_certs_vault_path` | `certs` / `{{ env }}/{{ redmine_domain }}` | Сертификат в Vault |

## Примечания

- Хендлеры: `Restart postgresql`, `Restart apache`.
