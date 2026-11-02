# nextcloud

Устанавливает [Nextcloud](https://nextcloud.com/): nginx + PHP-FPM 8.2 + MySQL, S3-хранилище (s3.cloud.ru), SSL из Vault, logrotate. Настройки по умолчанию оптимизированы под слабый сервер (2–4 ГБ RAM).

## Использование

```yaml
- hosts: nextcloud
  become: true
  roles:
    - nextcloud
```

## Переменные (основные)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `nextcloud_version` | `33.0.0` | Версия (для слабого сервера рассмотрите 28/29) |
| `nextcloud_domain` | `box.{{ domain }}` | Домен |
| `nextcloud_admin_user` | `admin` | Админ |
| `nextcloud_install_dir` / `nextcloud_data_dir` | `/var/www/nextcloud[/data]` | Каталог и данные |
| `nextcloud_php_version` | `8.2` | Версия PHP (8.2/8.3) |
| `nextcloud_db_name` / `nextcloud_db_user` | `nextcloud` | БД MySQL |
| `nextcloud_php_fpm_max_children` | `20` | workers PHP-FPM (правило: `max_children * memory_limit <= RAM * 0.8`) |
| `nextcloud_php_memory_limit` | `256M` | memory_limit PHP |
| `nextcloud_nginx_client_max_body_size` | `4G` | Лимит загрузки |
| `nextcloud_s3_endpoint` / `nextcloud_s3_bucket` | `s3.cloud.ru` / `nextcloud` | S3-хранилище |
| `nextcloud_s3_bucket_preview` | `nextcloud-preview` | Бакет превью |
| `nextcloud_s3_vault_mount` / `nextcloud_s3_vault_path` | `infra` / `{{ env }}/s3_secrets` | Ключи S3 в Vault |
| `nextcloud_vault_mount` / `nextcloud_vault_path` | `infra` / `{{ env }}/nextcloud` | Секреты в Vault |
| `nextcloud_enable_ssl` | `true` | TLS, сертификат из `certs` |
| `nextcloud_mail_smtpmode` | `sendmail` | Отправка почты |

Полный список (nginx-таймауты, gzip, PHP-FPM spare, logrotate) — в `defaults/main.yml`.

## Примечания

- Секреты (пароль БД, S3-ключи) — из Vault.
- Хендлеры: `Restart nginx`, `Restart PHP-FPM`.
